import os
from app import app
from db import db
from models import Product, ProductImage

# Directory where your images are stored
IMAGE_FOLDER = os.path.join(app.root_path, 'static', 'product_images')
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

def load_images_to_db():
    added = 0
    for filename in os.listdir(IMAGE_FOLDER):
        name, ext = os.path.splitext(filename)
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            continue

        parts = name.split('_')
        if len(parts) < 2 or not parts[0].isdigit():
            print(f"Skipping invalid file: {filename}")
            continue

        product_id = int(parts[0])
        is_primary = 1 if 'main' in parts[1].lower() else 0
        relative_path = f"product_images/{filename}"

        # Avoid duplicates
        exists = ProductImage.query.filter_by(ImageUrl=relative_path).first()
        if exists:
            print(f"Already in database: {filename}")
            continue

        new_image = ProductImage(
            ProductId=product_id,
            ImageUrl=relative_path,
            IsPrimary=is_primary
        )
        db.session.add(new_image)
        added += 1

    db.session.commit()
    print(f"{added} images added to the database.")

# Run it in app context
with app.app_context():
    load_images_to_db()
