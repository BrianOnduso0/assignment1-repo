from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Payment, Order
from extensions import db
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mpesa_bp = Blueprint('mpesa', __name__)

@mpesa_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback from Safaricom"""
    try:
        # Log the callback data
        callback_data = request.json
        logger.info(f"M-Pesa callback received: {json.dumps(callback_data)}")
        
        # Extract the necessary information from the callback
        body = callback_data.get('Body', {})
        stkCallback = body.get('stkCallback', {})
        checkout_request_id = stkCallback.get('CheckoutRequestID')
        result_code = stkCallback.get('ResultCode')
        result_desc = stkCallback.get('ResultDesc')
        
        # Find the payment with this checkout request ID
        payment = Payment.query.filter_by(mpesa_checkout_request_id=checkout_request_id).first()
        
        if not payment:
            logger.error(f"Payment not found for checkout request ID: {checkout_request_id}")
            return jsonify({"success": False, "message": "Payment not found"}), 404
        
        # Update the payment status based on the result code
        if result_code == 0:  # Success
            # Extract the transaction details
            callback_metadata = stkCallback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            mpesa_receipt = None
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                    break
            
            # Update payment
            payment.status = 'completed'
            payment.mpesa_receipt = mpesa_receipt
            payment.mpesa_result_code = str(result_code)
            payment.mpesa_result_desc = result_desc
            payment.payment_details = json.dumps(callback_data)
            
            # Update order status
            order = Order.query.get(payment.order_id)
            if order:
                order.status = 'paid'
            
            db.session.commit()
            logger.info(f"Payment {payment.id} updated to completed")
            
            return jsonify({"success": True, "message": "Payment completed successfully"}), 200
        else:
            # Payment failed
            payment.status = 'failed'
            payment.mpesa_result_code = str(result_code)
            payment.mpesa_result_desc = result_desc
            payment.payment_details = json.dumps(callback_data)
            
            db.session.commit()
            logger.info(f"Payment {payment.id} marked as failed: {result_desc}")
            
            return jsonify({"success": True, "message": "Payment failure recorded"}), 200
            
    except Exception as e:
        logger.exception(f"Error processing M-Pesa callback: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@mpesa_bp.route('/mpesa/query/<checkout_request_id>', methods=['GET'])
@jwt_required()
def query_payment_status(checkout_request_id):
    """Query the status of an M-Pesa payment"""
    from mpesa import MpesaAPI
    
    try:
        # Find the payment
        payment = Payment.query.filter_by(mpesa_checkout_request_id=checkout_request_id).first()
        
        if not payment:
            return jsonify({"success": False, "message": "Payment not found"}), 404
        
        # Check if the user is authorized to query this payment
        order = Order.query.get(payment.order_id)
        if not order or order.user_id != get_jwt_identity():
            return jsonify({"success": False, "message": "Unauthorized"}), 403
        
        # If payment is already completed or failed, return current status
        if payment.status in ['completed', 'failed']:
            return jsonify({
                "success": True,
                "payment_status": payment.status,
                "payment_details": {
                    "receipt": payment.mpesa_receipt,
                    "result_code": payment.mpesa_result_code,
                    "result_desc": payment.mpesa_result_desc
                }
            }), 200
        
        # Query the status from M-Pesa
        mpesa_api = MpesaAPI()
        result = mpesa_api.query_stk_status(checkout_request_id)
        
        # Update payment status if needed
        if result['success']:
            response_data = result['response']
            result_code = response_data.get('ResultCode')
            
            if result_code == 0:  # Success
                payment.status = 'completed'
                payment.mpesa_result_code = str(result_code)
                payment.mpesa_result_desc = response_data.get('ResultDesc', '')
                
                # Update order status
                if order:
                    order.status = 'paid'
                
                db.session.commit()
            elif result_code:  # Failed
                payment.status = 'failed'
                payment.mpesa_result_code = str(result_code)
                payment.mpesa_result_desc = response_data.get('ResultDesc', '')
                db.session.commit()
        
        return jsonify({
            "success": True,
            "payment_status": payment.status,
            "mpesa_result": result
        }), 200
        
    except Exception as e:
        logger.exception(f"Error querying payment status: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

