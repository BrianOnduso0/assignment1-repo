import requests
import base64
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MpesaAPI:
    def __init__(self):
        # Get credentials from environment variables with fallbacks
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = os.getenv('MPESA_BUSINESS_SHORTCODE', '174379')  # Default sandbox shortcode
        self.passkey = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')  # Default sandbox passkey
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://e5bd-102-213-48-10.ngrok-free.app')
        
        # Log configuration
        logger.info(f"M-Pesa API initialized with: shortcode={self.business_shortcode}, callback={self.callback_url}")
        if not self.consumer_key or not self.consumer_secret:
            logger.warning("M-Pesa API credentials missing! Using empty values which will cause API calls to fail.")
        
        self.transaction_type = "CustomerPayBillOnline"
        self.access_token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        self.query_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
        
    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        try:
            # For testing without actual credentials
            if not self.consumer_key or not self.consumer_secret:
                logger.warning("Using simulated access token due to missing credentials")
                return "simulated-access-token-for-testing"
                
            auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode("utf-8")
            headers = {
                "Authorization": f"Basic {auth}"
            }
            logger.info(f"Requesting access token from: {self.access_token_url}")
            response = requests.get(self.access_token_url, headers=headers)
            response_data = response.json()
            
            if 'access_token' in response_data:
                logger.info("Access token obtained successfully")
                return response_data['access_token']
            else:
                logger.error(f"Error getting access token: {response_data}")
                return None
        except Exception as e:
            logger.exception(f"Exception getting access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate the password for the STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password_bytes = password_str.encode('utf-8')
        return base64.b64encode(password_bytes).decode('utf-8'), timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push to customer's phone"""
        try:
            # Format phone number (remove leading 0 and add country code if needed)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]  # Remove the + sign
            
            logger.info(f"Initiating STK push for phone: {phone_number}, amount: {amount}")
            
            # For testing without actual API calls
            if not self.consumer_key or not self.consumer_secret:
                logger.warning("Using simulated STK push due to missing credentials")
                return {
                    "success": True,
                    "message": "SIMULATED STK push initiated successfully",
                    "checkout_request_id": "ws_CO_123456789012345678",
                    "response": {"CheckoutRequestID": "ws_CO_123456789012345678", "ResponseCode": "0", "ResponseDescription": "Success. Request accepted for processing"}
                }
                
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "message": "Failed to get access token"
                }
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": self.transaction_type,
                "Amount": int(amount),  # Amount must be an integer
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://e5bd-102-213-48-10.ngrok-free.app",
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            logger.info(f"STK push payload: {json.dumps(payload)}")
            
            # Make the request
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response_data = response.json()
            logger.info(f"STK push response: {json.dumps(response_data)}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "STK push initiated successfully",
                    "checkout_request_id": response_data.get("CheckoutRequestID"),
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to initiate STK push: {response_data.get('errorMessage', 'Unknown error')}",
                    "response": response_data
                }
        except Exception as e:
            logger.exception(f"Exception initiating STK push: {str(e)}")
            return {
                "success": False,
                "message": f"Exception: {str(e)}"
            }
    
    def query_stk_status(self, checkout_request_id):
        """Query the status of an STK push transaction"""
        try:
            # For testing without actual API calls
            if not self.consumer_key or not self.consumer_secret:
                logger.warning("Using simulated query response due to missing credentials")
                return {
                    "success": True,
                    "message": "SIMULATED Query successful",
                    "response": {"ResultCode": "0", "ResultDesc": "The service request is processed successfully."}
                }
                
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "message": "Failed to get access token"
                }
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            # Make the request
            response = requests.post(self.query_url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Query successful",
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "message": f"Query failed: {response_data.get('errorMessage', 'Unknown error')}",
                    "response": response_data
                }
        except Exception as e:
            logger.exception(f"Exception querying STK status: {str(e)}")
            return {
                "success": False,
                "message": f"Exception: {str(e)}"
            }

