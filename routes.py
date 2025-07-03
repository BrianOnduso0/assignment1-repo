from resources import UserRegistration, UserLogin, ProductResource, ProductDetailResource, OrderResource, WishlistResource, PaymentResource

def initialize_routes(api):
  api.add_resource(UserRegistration, '/register')
  api.add_resource(UserLogin, '/login')
  api.add_resource(ProductResource, '/products')
  api.add_resource(ProductDetailResource, '/products/<int:product_id>')
  api.add_resource(OrderResource, '/orders')
  api.add_resource(WishlistResource, '/wishlist', '/wishlist/<int:wishlist_id>')
  api.add_resource(PaymentResource, '/payments', '/payments/<int:order_id>')

