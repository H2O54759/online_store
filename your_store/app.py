from flask import Flask, render_template, redirect, url_for, session, request, flash
from config import Config, SITE_SETTINGS
import os
import logging
import sys
import atexit

from db import db
from models import Product, Category, ProductImage
from forms import ProductForm

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = Config.SECRET_KEY or 'replace-with-a-secure-random-key'
db.init_app(app)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clear existing handlers (if any)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler('cleanup.log')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)

@app.context_processor
def inject_site_settings():
    return dict(site_settings=SITE_SETTINGS)

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    images = product.images
    image_urls = [img.ImageUrl for img in images] if images else []
    return render_template('product.html', product=product, images=images, image_urls=image_urls)

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('home'))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f"Added {product.Name} to cart.", "success")
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0.0
    for product_id, qty in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = float(product.Price) * qty
            total_price += item_total
            cart_items.append({'product': product, 'quantity': qty, 'total': item_total})
    return render_template('cart.html', cart_items=cart_items, total_price=round(total_price, 2))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    action = request.form.get('action')
    cart = session.get('cart', {})
    key = str(product_id)
    if key not in cart:
        flash("Item not in cart.", "warning")
        return redirect(url_for('cart'))

    if action == 'increase':
        cart[key] += 1
    elif action == 'decrease':
        cart[key] = max(1, cart[key] - 1)
    elif action == 'remove':
        cart.pop(key, None)
    else:
        flash("Invalid action.", "warning")

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    products = []

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            products.append({
                'product': product,
                'quantity': quantity,
                'price': float(product.Price),
                'subtotal': quantity * float(product.Price)
            })

    total_amount = sum(item['subtotal'] for item in products)

    return render_template('checkout.html', products=products, total_amount=total_amount)

# --- Admin routes ---

@app.route('/admin')
def admin_dashboard():
    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    categories = Category.query.order_by(Category.Name).all()
    if not categories:
        default_cats = ["Rifle Accessories", "Pistol Accessories", "Outdoors Gear", "Misc."]
        db.session.add_all([Category(Name=name) for name in default_cats])
        db.session.commit()
        categories = Category.query.order_by(Category.Name).all()

    form.category.choices = [(c.CategoryId, c.Name) for c in categories]

    if form.validate_on_submit():
        product = Product(
            Name=form.name.data,
            Description=form.description.data,
            Price=form.price.data,
            Stock=form.stock.data,
            CategoryId=form.category.data
        )
        db.session.add(product)
        db.session.flush()  # To assign ProductId before commit

        # Handle primary image
        if form.image_url.data:
            # Demote existing primary images (should be none for new product)
            ProductImage.query.filter_by(ProductId=product.ProductId, IsPrimary=True).update({'IsPrimary': False})
            db.session.add(ProductImage(ProductId=product.ProductId, ImageUrl=form.image_url.data, IsPrimary=True))

        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_product.html', form=form)

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.Name).all()
    form = ProductForm(obj=product)
    form.category.choices = [(c.CategoryId, c.Name) for c in categories]

    if form.validate_on_submit():
        product.Name = form.name.data
        product.Description = form.description.data
        product.Price = form.price.data
        product.Stock = form.stock.data
        product.CategoryId = form.category.data

        if form.image_url.data:
            # Demote existing primary images
            ProductImage.query.filter_by(ProductId=product.ProductId, IsPrimary=True).update({'IsPrimary': False})
            existing_image = ProductImage.query.filter_by(ProductId=product.ProductId, ImageUrl=form.image_url.data).first()
            if existing_image:
                existing_image.IsPrimary = True
            else:
                db.session.add(ProductImage(ProductId=product.ProductId, ImageUrl=form.image_url.data, IsPrimary=True))

        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Pre-fill the primary image URL in the form
    primary_img = ProductImage.query.filter_by(ProductId=product.ProductId, IsPrimary=True).first()
    if primary_img:
        form.image_url.data = primary_img.ImageUrl

    return render_template('admin_edit_product.html', form=form, product=product)

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'danger')
    return redirect(url_for('admin_dashboard'))

# --- Cleanup duplicate primary images job ---
def cleanup_duplicate_primary_images():
    with app.app_context():
        duplicates = (
            db.session.query(ProductImage.ProductId)
            .filter(ProductImage.IsPrimary == True)
            .group_by(ProductImage.ProductId)
            .having(db.func.count(ProductImage.ImageId) > 1)
            .all()
        )
        logger.info(f"Found {len(duplicates)} products with duplicate primary images.")

        for (product_id,) in duplicates:
            primary_images = ProductImage.query.filter_by(ProductId=product_id, IsPrimary=True).order_by(ProductImage.ImageId).all()
            # Keep the first primary image, demote others
            for img in primary_images[1:]:
                img.IsPrimary = False
                logger.info(f"Demoted image {img.ImageId} for product {product_id} from primary.")

        db.session.commit()
        logger.info("Cleanup job completed.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_duplicate_primary_images, trigger='cron', hour=3, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    logger.info("Scheduler started with daily 3 AM cleanup job.")

if __name__ == '__main__':
    with app.app_context():
        start_scheduler()
        # Uncomment to run cleanup immediately at startup
        # cleanup_duplicate_primary_images()

    app.run(host='127.0.0.1', port=5000, debug=True)
