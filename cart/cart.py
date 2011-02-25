import datetime
import models

CART_ID = 'CART-ID'

class ItemAlreadyExists(Exception):
	pass

class ItemDoesNotExist(Exception):
	pass

class Cart:
	def __init__(self, request):
		cart_id = request.session.get(CART_ID)
		if cart_id:
			try:
				cart = models.Cart.objects.get(id=cart_id, checked_out=False)
			except models.Cart.DoesNotExist:
				cart = self.new(request)
		else:
			cart = self.new(request)
		self.cart = cart

	def __iter__(self):
		for item in self.cart.item_set.all():
			yield item

	def new(self, request):
		cart = models.Cart(creation_date=datetime.datetime.now())
		cart.save()
		request.session[CART_ID] = cart.id
		return cart

	def add(self, product, unit_price, quantity=1, variation=''):
		try:
			item = models.Item.objects.get(cart=self.cart, product=product,)
		except models.Item.DoesNotExist:
			item = models.Item()
			item.cart = self.cart
			item.product = product
			item.unit_price = unit_price
			item.quantity = quantity
			item.variations = variation #saves the variation string...
			item.save()
		else:
            #is the same variation the added one? or a different variation?
            #it could be a mix of variations, since it can be more than one.
            if variation == item.variations:
                #Its EXACTLY THE SAME combination. increment it
                item.quantity += quantity
            else:
                #add a new combination (example, Size:Large, Color:red)
                item.variations = variation #saves the variation string...
			item.save()

	def remove(self, item):
        #here we dont worry about variations.
		try:
			item = models.Item.objects.get(pk=item.pk)
		except models.Item.DoesNotExist:
			raise ItemDoesNotExist
		else:
			item.delete()
	
	def update(self, product, unit_price, quantity, variation=''):
		try:
			item = models.Item.objects.get(
				cart=self.cart,
				product=product,
			)
			item.cart = self.cart
			item.product = product
			item.unit_price = unit_price
			item.quantity = quantity
			item.variations = variation #if no variation is passed, the default is empty.
			item.save(force_update = True)
		except models.Item.DoesNotExist:
			raise ItemDoesNotExist
	
	def clear(self):
		for item in self.cart.item_set.all():
			item.delete()
	
	# There's all sort of info you might want to easily get from your cart
	
	def getQuantity(self, product):
		try: 
			item = models.Item.objects.get(cart = self.cart, product = product)
			return item.quantity
			
		except models.Item.DoesNotExist:
			raise ItemDoesNotExist
	
	def checkout_cart(self):
		self.cart.checked_out = True
		self.cart.save()
		return True

	def total(self):
		total = 0
		for item in self.cart.item_set.all():
			total += item.total_price
		return total
		
	def itemCount(self):
		total = 0
		for item in self.cart.item_set.all():
			total += item.quantity
		return total
		
	def hasItems(self):
		return self.itemCount() > 0
		
def cart_processor(request):
	cart_id = request.session.get(CART_ID)
	if cart_id:
		return {'cart' : Cart(request),}
	else:
		return {'cart' : None,}
