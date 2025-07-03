import os
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import Vendor, Product
from extensions import db

class VendorRegistration(Resource):
    def post(self):
        data = request.get_json()
        vendor = Vendor(
            username=data['username'],
            email=data['email'],
            business_name=data['business_name'],
            business_description=data.get('business_description', ''),
            contact_phone=data.get('contact_phone', '')
        )
        vendor.set_password(data['password'])
        db.session.add(vendor)
        db.session.commit()
        return {'message': 'Vendor registered successfully'}, 201

class VendorLogin(Resource):
    def post(self):
        data = request.get_json()
        vendor = Vendor.query.filter_by(username=data['username']).first()
        if vendor and vendor.check_password(data['password']):
            access_token = create_access_token(identity={'id': vendor.id, 'type': 'vendor'})
            return {'access_token': access_token}, 200
        return {'message': 'Invalid credentials'}, 401

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class VendorProductResource(Resource):
    @jwt_required()
    def post(self):
        # Check if the user is a vendor
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('type') == 'vendor':
            vendor_id = identity.get('id')
        else:
            return {'message': 'Unauthorized. Only vendors can add products.'}, 403
        
        # Handle form data for product details and image
        product_data = {}
        if 'name' in request.form:
            product_data['name'] = request.form['name']
        if 'description' in request.form:
            product_data['description'] = request.form['description']
        if 'price' in request.form:
            product_data['price'] = float(request.form['price'])
        if 'stock' in request.form:
            product_data['stock'] = int(request.form['stock'])
        
        # Validate required fields
        if not all(key in product_data for key in ['name', 'price', 'stock']):
            return {'message': 'Missing required product information'}, 400
        
        # Create product
        new_product = Product(
            name=product_data['name'],
            description=product_data.get('description', ''),
            price=product_data['price'],
            stock=product_data['stock'],
            vendor_id=vendor_id
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Store the relative URL
                new_product.image_url = f'/static/uploads/{filename}'
        
        db.session.add(new_product)
        db.session.commit()
        
        return {
            'message': 'Product added successfully',
            'product_id': new_product.id,
            'image_url': new_product.image_url
        }, 201

    @jwt_required()
    def get(self):
        # Check if the user is a vendor
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('type') == 'vendor':
            vendor_id = identity.get('id')
        else:
            return {'message': 'Unauthorized. Only vendors can view their products.'}, 403
        
        products = Product.query.filter_by(vendor_id=vendor_id).all()
        return {
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'price': p.price,
                    'stock': p.stock,
                    'image_url': p.image_url,
                    'created_at': p.created_at.isoformat() if p.created_at else None
                } for p in products
            ]
        }

class VendorProductDetailResource(Resource):
    @jwt_required()
    def get(self, product_id):
        # Check if the user is a vendor
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('type') == 'vendor':
            vendor_id = identity.get('id')
        else:
            return {'message': 'Unauthorized. Only vendors can view their product details.'}, 403
        
        product = Product.query.filter_by(id=product_id, vendor_id=vendor_id).first()
        if not product:
            return {'message': 'Product not found or not owned by this vendor'}, 404
        
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'image_url': product.image_url,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }
    
    @jwt_required()
    def put(self, product_id):
        # Check if the user is a vendor
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('type') == 'vendor':
            vendor_id = identity.get('id')
        else:
            return {'message': 'Unauthorized. Only vendors can update their products.'}, 403
        
        product = Product.query.filter_by(id=product_id, vendor_id=vendor_id).first()
        if not product:
            return {'message': 'Product not found or not owned by this vendor'}, 404
        
        # Handle form data for product details and image
        if 'name' in request.form:
            product.name = request.form['name']
        if 'description' in request.form:
            product.description = request.form['description']
        if 'price' in request.form:
            product.price = float(request.form['price'])
        if 'stock' in request.form:
            product.stock = int(request.form['stock'])
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save the file
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Store the relative URL
                product.image_url = f'/static/uploads/{filename}'
        
        db.session.commit()
        
        return {
            'message': 'Product updated successfully',
            'product_id': product.id,
            'image_url': product.image_url
        }
    
    @jwt_required()
    def delete(self, product_id):
        # Check if the user is a vendor
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('type') == 'vendor':
            vendor_id = identity.get('id')
        else:
            return {'message': 'Unauthorized. Only vendors can delete their products.'}, 403
        
        product = Product.query.filter_by(id=product_id, vendor_id=vendor_id).first()
        if not product:
            return {'message': 'Product not found or not owned by this vendor'}, 404
        
        db.session.delete(product)
        db.session.commit()
        
        return {'message': 'Product deleted successfully'}

