from app import create_app
from extensions import db
from models import User, Vendor, Product, Order, OrderItem, Wishlist, Payment

# Create the application instance
app = create_app()

# Use the app context
with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    print("Database schema has been reset successfully!")
    print("All tables have been recreated with the current model definitions.")

