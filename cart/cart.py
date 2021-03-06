import datetime
import models

import decimal
from decimal import *

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

	def add(self, product, unit_price, quantity=1, unit_weight=0, variation=''):
		items = models.Item.objects.filter(cart=self.cart, object_id=product.pk)
		foundIt = False
		for item in items:
			#iteramos cada uno...
			if variation == item.variations:
				#Its EXACTLY THE SAME combination. increment it
				item.quantity += quantity
				#Now we need to get discounts for volume sale.
				if product.descuento_por_volumen:
					dpv = product.get_discount_for(item.quantity)
					item.unit_price = unit_price - (unit_price*(dpv/100))
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
			#Now we need to get discounts for volume sale.
			if product.descuento_por_volumen:
				dpv = product.get_discount_for(item.quantity)
				item.unit_price = unit_price - (unit_price*(dpv/100))
			else:
				item.unit_price = unit_price
			item.unit_weight = unit_weight
			item.product = product #the same product...
			item.cart = self.cart
			item.save()

	def remove(self, item_id):
		#here we dont worry about variations.
		try:
			item = models.Item.objects.get(pk=item_id)
		except models.Item.DoesNotExist:
			pass #Si ya no existe, entonces no es necesario quitarlo.
		    #raise ItemDoesNotExist #Esto lanza un error 500. Como manejar esto para que al recargar la pagina con un GET para quitar un item que ya no existe en el carrito no muestre errores?
		else:
			item.delete()

	#This will only update the item qty (the item is the cart-item id, not the product)
	#this in order to support multiple product with variations
	#I dont need to update prices nor weights.
	def update(self, item_id, quantity):
		if item_id > 0:
			try:
				item = models.Item.objects.get(cart=self.cart, pk=item_id)
				if (quantity <= 0):
					item.delete()
				else:
					item.quantity = quantity
					#Now we need to get discounts for volume sale.
					product = item.get_product()
					if product.descuento_por_volumen:
						dpv = product.get_discount_for(quantity)
						if product.tieneDescuentoValido:
							unit_price = product.precioConDescuento
						else:
							unit_price = product.precio
						unit_price = Decimal(unit_price)
						item.unit_price = unit_price - (unit_price*(dpv/100))
					item.save(force_update = True)
			except models.Item.DoesNotExist:
				print "ITEM TO UPDATE DOES NOT EXISTS [%d]"%item_id
				#raise ItemDoesNotExist
		else:
			print "ITEM ID passed was ZERO. Unable to update"

	def updatePriceAndWeight(self, item_id, price, weight):
		if item_id > 0:
			try:
				item = models.Item.objects.get(cart=self.cart, pk=item_id)
				item.unit_price = price
				item.unit_weight= weight
				item.save(force_update = True)
			except models.Item.DoesNotExist:
				print "ITEM TO UPDATE DOES NOT EXISTS [%d]"%item_id
				#raise ItemDoesNotExist
		else:
			print "ITEM ID passed was ZERO. Unable to update"
	
	def clear(self):
		for item in self.cart.item_set.all():
			item.delete()
	
	# There's all sort of info you might want to easily get from your cart
	
	def getQuantity(self, product):
		try: 
			item = models.Item.objects.get(cart = self.cart, product = product)
			return item.quantity
			
		except models.Item.DoesNotExist:
			pass
			#raise ItemDoesNotExist
	
	def checkout_cart(self):
		self.cart.checked_out = True
		self.cart.save()
		return True

	def total(self):
		total = 0
		for item in self.cart.item_set.all():
			total += item.total_price
		return total

	def total_weight(self):
		tw = 0
		for item in self.cart.item_set.all():
			tw += item.total_weight
		return tw


	def itemLines(self):
		total = 0
		total = self.cart.item_set.count()
		return total

	def itemCount(self):
		total = 0
		for item in self.cart.item_set.all():
			total += item.quantity
		return total

	def num_packages(self, maxPorPaquete):
		num = self.itemCount() / Decimal(maxPorPaquete) #We need one of the operands to be decimal in order to get a decimal result.
		#we want to round to up not to down. Example: round(1.2) rounds to 1.0 and we want round to 2.0
		intPart = int(num)
		decPart = num - intPart
		if decPart >= 0.1:
			intPart += 1
		#print 'carrito. count/max=%s   count:%s, maxPorPaquete:%s, decPart:%s, intPart:%s'%(num, self.itemCount(), maxPorPaquete, decPart, intPart)
		return intPart
		
	def hasItems(self):
		return self.itemCount() > 0
		
def cart_processor(request):
	cart_id = request.session.get(CART_ID)
	if cart_id:
		return {'cart' : Cart(request),}
	else:
		return {'cart' : None,}
