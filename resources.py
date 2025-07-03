from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Product, Order, OrderItem, Wishlist, Payment
from extensions import db
import json
import logging
from mpesa import MpesaAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return {'message': 'User created successfully'}, 201

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}, 200
        return {'message': 'Invalid credentials'}, 401

class ProductResource(Resource):
    @jwt_required()
    def post(self):
        # This endpoint is now deprecated in favor of VendorProductResource
        return {'message': 'This endpoint is deprecated. Vendors should use /vendor/products'}, 400

    def get(self):
        products = Product.query.all()
        return {'products': [
            {
                'id': p.id, 
                'name': p.name, 
                'description': p.description,
                'price': p.price, 
                'stock': p.stock,
                'image_url': p.image_url,
                'vendor_id': p.vendor_id
            } for p in products
        ]}

class ProductDetailResource(Resource):
    def get(self, product_id):
        product = Product.query.get_or_404(product_id)
        return {
            'id': product.id, 
            'name': product.name, 
            'description': product.description,
            'price': product.price, 
            'stock': product.stock,
            'image_url': product.image_url,
            'vendor_id': product.vendor_id
        }

class OrderResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            if not data:
                logger.error("No JSON data received in request")
                return {'message': 'No data provided'}, 400
                
            logger.info(f"Received order data: {data}")
            
            # Validate required fields
            if 'total' not in data:
                logger.error("Missing 'total' field in order data")
                return {'message': 'Missing required field: total'}, 422
                
            if 'items' not in data or not isinstance(data['items'], list) or len(data['items']) == 0:
                logger.error("Missing or invalid 'items' field in order data")
                return {'message': 'Missing or invalid field: items (must be a non-empty array)'}, 422
            
            # Validate each item
            for i, item in enumerate(data['items']):
                if 'product_id' not in item:
                    logger.error(f"Missing 'product_id' in item {i}")
                    return {'message': f'Missing product_id in item {i}'}, 422
                if 'quantity' not in item:
                    logger.error(f"Missing 'quantity' in item {i}")
                    return {'message': f'Missing quantity in item {i}'}, 422
                if 'price' not in item:
                    logger.error(f"Missing 'price' in item {i}")
                    return {'message': f'Missing price in item {i}'}, 422
            
            user_id = get_jwt_identity()
            logger.info(f"User ID: {user_id}")
            
            # Create new order
            new_order = Order(user_id=user_id, status='pending', total=data['total'])
            db.session.add(new_order)
            db.session.commit()
            logger.info(f"Created new order with ID: {new_order.id}")

            # Process order items and update stock
            for item in data['items']:
                # Get the product
                product = Product.query.get(item['product_id'])
                if not product:
                    logger.warning(f"Product not found: {item['product_id']}")
                    continue
                    
                # Check if enough stock is available
                if product.stock < item['quantity']:
                    logger.warning(f"Not enough stock for product {product.name}: {product.stock} available, {item['quantity']} requested")
                    return {'message': f'Not enough stock for {product.name}'}, 400
                    
                # Update product stock
                product.stock -= item['quantity']
                logger.info(f"Updated stock for product {product.name}: {product.stock + item['quantity']} -> {product.stock}")
                
                # Create order item
                order_item = OrderItem(
                    order_id=new_order.id, 
                    product_id=item['product_id'],
                    quantity=item['quantity'], 
                    price=item['price']
                )
                db.session.add(order_item)
                logger.info(f"Added order item: product_id={item['product_id']}, quantity={item['quantity']}")
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Order {new_order.id} created successfully")
            return {'message': 'Order placed successfully', 'order_id': new_order.id}, 201
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error creating order: {str(e)}")
            return {'message': f'Error creating order: {str(e)}'}, 500

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=user_id).all()
        return {'orders': [{'id': o.id, 'status': o.status, 'total': o.total} for o in orders]}

class WishlistResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        try:
            wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
            return {'wishlist': [{'id': item.id, 'product_id': item.product_id} for item in wishlist_items]}
        except Exception as e:
            logger.exception(f"Error fetching wishlist: {str(e)}")
            return {'message': 'Error fetching wishlist', 'error': str(e)}, 500

    @jwt_required()
    def post(self):
        data = request.get_json()
        user_id = get_jwt_identity()
        product_id = data['product_id']
        
        existing_item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing_item:
            return {'message': 'Item already in wishlist'}, 400
        
        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        return {'message': 'Item added to wishlist'}, 201

    @jwt_required()
    def delete(self, wishlist_id):
        user_id = get_jwt_identity()
        item = Wishlist.query.filter_by(id=wishlist_id, user_id=user_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return {'message': 'Item removed from wishlist'}, 200
        return {'message': 'Item not found'}, 404

class PaymentResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            logger.info(f"Received payment data: {data}")
            order_id = data['order_id']
            amount = data['amount']
            payment_method = data['payment_method']

            order = Order.query.get(order_id)
            if not order:
                logger.warning(f"Order not found: {order_id}")
                return {'message': 'Order not found'}, 404

            if order.user_id != get_jwt_identity():
                logger.warning(f"Unauthorized payment attempt: user_id={get_jwt_identity()}, order.user_id={order.user_id}")
                return {'message': 'Unauthorized'}, 403

            # Handle M-Pesa payment
            if payment_method == 'mpesa':
                phone_number = data.get('phone_number')
                if not phone_number:
                    logger.warning("Phone number missing for M-Pesa payment")
                    return {'message': 'Phone number is required for M-Pesa payments'}, 400
                
                logger.info(f"Processing M-Pesa payment: phone={phone_number}, amount={amount}")
                
                # Create a pending payment record
                payment = Payment(
                    order_id=order_id,
                    amount=amount,
                    status='pending',
                    payment_method='mpesa',
                    mpesa_phone=phone_number
                )
                db.session.add(payment)
                db.session.commit()
                logger.info(f"Created pending payment record: id={payment.id}")
                
                try:
                    # Initialize M-Pesa API
                    mpesa_api = MpesaAPI()
                    
                    # Initiate STK push
                    account_reference = f"Order #{order_id}"
                    transaction_desc = f"Payment for Order #{order_id}"
                    
                    logger.info(f"Initiating M-Pesa STK push: phone={phone_number}, amount={amount}")
                    result = mpesa_api.initiate_stk_push(
                        phone_number=phone_number,
                        amount=amount,
                        account_reference=account_reference,
                        transaction_desc=transaction_desc
                    )
                    logger.info(f"M-Pesa STK push result: {result}")
                    
                    if result['success']:
                        # Update payment with checkout request ID
                        checkout_request_id = result['checkout_request_id']
                        payment.mpesa_checkout_request_id = checkout_request_id
                        db.session.commit()
                        logger.info(f"Updated payment with checkout_request_id: {checkout_request_id}")
                        
                        return {
                            'message': 'M-Pesa payment initiated. Please check your phone to complete the payment.',
                            'payment_id': payment.id,
                            'checkout_request_id': checkout_request_id,
                            'status': 'pending'
                        }, 200
                    else:
                        # Mark payment as failed
                        payment.status = 'failed'
                        payment.mpesa_result_desc = result['message']
                        db.session.commit()
                        logger.warning(f"M-Pesa payment initiation failed: {result['message']}")
                        
                        return {
                            'message': 'Failed to initiate M-Pesa payment',
                            'error': result['message'],
                            'payment_id': payment.id,
                            'status': 'failed'
                        }, 400
                except Exception as mpesa_error:
                    logger.exception(f"M-Pesa API error: {str(mpesa_error)}")
                    payment.status = 'failed'
                    payment.mpesa_result_desc = str(mpesa_error)
                    db.session.commit()
                    return {'message': f'M-Pesa API error: {str(mpesa_error)}'}, 500
                
            else:
                # Handle other payment methods (credit card, PayPal, etc.)
                logger.info(f"Processing {payment_method} payment: amount={amount}")
                payment = Payment(
                    order_id=order_id, 
                    amount=amount, 
                    status='completed', 
                    payment_method=payment_method
                )
                
                db.session.add(payment)
                order.status = 'paid'
                order.payment_id = payment.id
                db.session.commit()
                logger.info(f"Payment completed successfully: id={payment.id}")
                
                return {
                    'message': 'Payment processed successfully', 
                    'payment_id': payment.id,
                    'payment_method': payment_method,
                    'status': 'completed'
                }, 200
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Payment processing error: {str(e)}")
            return {'message': f'Payment processing error: {str(e)}'}, 500

    @jwt_required()
    def get(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return {'message': 'Order not found'}, 404

        if order.user_id != get_jwt_identity():
            return {'message': 'Unauthorized'}, 403

        payment = Payment.query.filter_by(order_id=order_id).first()
        if payment:
            response = {
                'payment_id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'payment_date': payment.payment_date.isoformat(),
                'payment_method': payment.payment_method
            }
            
            # Add M-Pesa specific details if available
            if payment.payment_method == 'mpesa':
                mpesa_details = {
                    'phone_number': payment.mpesa_phone,
                    'checkout_request_id': payment.mpesa_checkout_request_id,
                    'receipt': payment.mpesa_receipt,
                    'result_code': payment.mpesa_result_code,
                    'result_description': payment.mpesa_result_desc
                }
                response['mpesa_details'] = mpesa_details
                
            return response
        return {'message': 'No payment found for this order'}, 404

