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
		items = models.Item.objects.filter(cart=self.cart, object_id=product.pk)
		foundIt = False
		for item in items:
			#iteramos cada uno...
			#print 'ITEM RETURNED: %s | %s | %s '%(item.product.nombre,item.variations,item.pk)
			if variation == item.variations:
				#Its EXACTLY THE SAME combination. increment it
				#print '[  EQUAL  ] Item variation = %s | passed variation:%s'%(item.variations, variation)
				item.quantity += quantity
				item.save() #The item is inside the for loop... thats why we save it here
				foundIt = True
				break #exit the for loop because we found an exact match... and it should not be another (duplicated item and variation)
		#print "For loop finished!"
		if not foundIt:
			#hey, the for loop cycle is completed and we did not found the item...
			#add a new combination (example, Size:Large, Color:red)
			item = models.Item() # Create a new one because it is different in variation.
			item.variations = variation #saves the variation string...
			item.quantity = quantity
			item.unit_price = unit_price
			item.product = product #the same product...
			item.cart = self.cart
			item.save()
		#else: #item does not exists
			#item = models.Item()
			#item.cart = self.cart
			#item.product = product
			#item.unit_price = unit_price
			#item.quantity = quantity
			#item.variations = variation #saves the variation string...
			#item.save()

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
