# config.py
import os
import urllib

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Updated MS SQL connection params with your actual server/database/credentials
    params = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=tcp:sql2k2201.discountasp.net;"
        "DATABASE=SQL2022_96222_tba;"
        "UID=SQL2022_96222_tba_user;"
        "PWD=Alfred47114711$;"
        "TrustServerCertificate=yes;"
    )

    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'  # Needed for session management

# === Site-Wide Style Settings ===
SITE_SETTINGS = {
    'primary_color': '#007bff',
    'font_family': 'Arial, sans-serif',
    'font_size': '16px',
    'border_style': '1px solid #ddd',
    'default_image': 'img/default.jpg',
    'button_texts': {
        'add_to_cart': 'Add to Cart',
        'remove': 'Remove',
        'checkout': 'Proceed to Checkout'
    }
}

# Optional test products
PRODUCTS = [
    {
        'id': 1,
        'name': 'Product 1',
        'price': 29.99,
        'description': 'This is product 1.',
        'images': ['product1a.jpg', 'product1b.jpg', 'product1c.jpg']
    },
    {
        'id': 2,
        'name': 'Product 2',
        'price': 49.99,
        'description': 'This is product 2.',
        'images': ['product2a.jpg', 'product2b.jpg', 'product2c.jpg']
    },
    {
        'id': 3,
        'name': 'Product 3',
        'price': 19.99,
        'description': 'This is product 3.',
        'images': ['product3a.jpg', 'product3b.jpg', 'product3c.jpg']
    }
]

# Automatically set a main image for each product
for product in PRODUCTS:
    product['image'] = product['images'][0] if product.get('images') else SITE_SETTINGS['default_image']
