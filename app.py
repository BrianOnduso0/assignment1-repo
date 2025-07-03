from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from extensions import db, jwt
from resources import UserRegistration, UserLogin, ProductResource, ProductDetailResource, OrderResource, WishlistResource, PaymentResource
from vendor_resources import VendorRegistration, VendorLogin, VendorProductResource, VendorProductDetailResource
from mpesa_routes import mpesa_bp
from contact_routes import contact_bp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    # Enable CORS for all routes with proper credentials support
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '073cfa0a88a0d16ca567abbec011ef95523c1b24531b1dc7d108acb9a509bc0c')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

    db.init_app(app)
    Migrate(app, db)
    jwt.init_app(app)

    # Register the M-Pesa blueprint
    app.register_blueprint(mpesa_bp)
    app.register_blueprint(contact_bp)

    api = Api(app)

    # User routes
    api.add_resource(UserRegistration, '/register')
    api.add_resource(UserLogin, '/login')
    api.add_resource(ProductResource, '/products')
    api.add_resource(ProductDetailResource, '/products/<int:product_id>')
    api.add_resource(OrderResource, '/orders')
    api.add_resource(WishlistResource, '/wishlist', '/wishlist/<int:wishlist_id>')
    api.add_resource(PaymentResource, '/payments', '/payments/<int:order_id>')

    # Vendor routes
    api.add_resource(VendorRegistration, '/vendor/register')
    api.add_resource(VendorLogin, '/vendor/login')
    api.add_resource(VendorProductResource, '/vendor/products')
    api.add_resource(VendorProductDetailResource, '/vendor/products/<int:product_id>')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

