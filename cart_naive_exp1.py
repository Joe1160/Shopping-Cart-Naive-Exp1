from decimal import Decimal
from django.conf import settings
# 請根據你的專案路徑修改 Product 的匯入來源
from shop.models import Product 

class Cart:
    def __init__(self, request):
        """
        初始化購物車
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # 如果 session 中沒有購物車，則建立一個空的
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        將商品加入購物車或更新數量
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price) # 儲存字串以利於 JSON 序列化
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        self.save()

    def save(self):
        """
        標記 session 為已修改，確保 Django 會將其儲存
        """
        self.session.modified = True

    def remove(self, product):
        """
        從購物車中移除商品
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        迭代購物車中的品項，並從資料庫抓取最新的商品物件
        """
        product_ids = self.cart.keys()
        # 獲取商品物件並加入到購物車副本中
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        計算購物車內所有商品的總數量
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        計算購物車內所有商品的總金額
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        清空購物車 session
        """
        del self.session[settings.CART_SESSION_ID]
        self.save() 
