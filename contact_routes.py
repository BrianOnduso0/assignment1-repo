from flask import Blueprint, request, jsonify
from email_service import EmailService

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['POST'])
def submit_contact_form():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
                
        # Get form data
        name = data['name']
        email = data['email']
        subject = data['subject']
        message = data['message']
        phone = data.get('phone', '')  # Optional field
        
        # Send email
        email_service = EmailService()
        result = email_service.send_contact_form(
            name=name,
            email=email,
            subject=subject,
            message=message,
            phone=phone
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully!'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
            
    except Exception as e:
        print(f"Error processing contact form: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500

