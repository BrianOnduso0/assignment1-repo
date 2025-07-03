from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(128))

  def set_password(self, password):
      self.password_hash = generate_password_hash(password)

  def check_password(self, password):
      return check_password_hash(self.password_hash, password)

class Vendor(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(128))
  business_name = db.Column(db.String(100), nullable=False)
  business_description = db.Column(db.Text)
  contact_phone = db.Column(db.String(20))
  registration_date = db.Column(db.DateTime, default=datetime.utcnow)

  def set_password(self, password):
      self.password_hash = generate_password_hash(password)

  def check_password(self, password):
      return check_password_hash(self.password_hash, password)

class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  description = db.Column(db.Text)
  price = db.Column(db.Float, nullable=False)
  stock = db.Column(db.Integer, nullable=False)
  vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
  image_url = db.Column(db.String(255))
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  status = db.Column(db.String(20), nullable=False)
  total = db.Column(db.Float, nullable=False)
  payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
  
class OrderItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  price = db.Column(db.Float, nullable=False)

class Wishlist(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  added_date = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  status = db.Column(db.String(20), nullable=False)  # 'pending', 'completed', 'failed'
  payment_date = db.Column(db.DateTime, default=datetime.utcnow)
  payment_method = db.Column(db.String(50), nullable=False)
  payment_details = db.Column(db.Text)  # For storing general payment details
  
  # M-Pesa specific fields
  mpesa_phone = db.Column(db.String(20))  # Phone number used for payment
  mpesa_receipt = db.Column(db.String(50))  # M-Pesa receipt number
  mpesa_checkout_request_id = db.Column(db.String(100))  # Checkout request ID for tracking
  mpesa_result_code = db.Column(db.String(10))  # Result code from M-Pesa
  mpesa_result_desc = db.Column(db.String(255))  # Result description from M-Pesa

