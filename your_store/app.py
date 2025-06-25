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

# --- Flask app setup ---
app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = Config.SECRET_KEY or 'replace-with-a-secure-random-key'
db.init_app(app)

# --- Logging setup: log to file and console ---
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

# --- Context processor for site-wide settings ---
@app.context_processor
def inject_site_settings():
    return dict(site_settings=SITE_SETTINGS)

# --- Routes ---

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    images = product.images  # full ORM objects
    image_urls = [img.ImageUrl for img in images] if images else []
    return render_template('product.html', product=product, images=images, image_urls=image_urls)


@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        return "Product not found", 404
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0
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
        return redirect(url_for('cart'))
    if action == 'increase':
        cart[key] += 1
    elif action == 'decrease':
        cart[key] = max(1, cart[key] - 1)
    elif action == 'remove':
        cart.pop(key, None)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        return "<h1>Thank you for your order!</h1><p><a href='/'>Return home</a></p>"
    return """
    <h1>Checkout</h1>
    <form method="post">
        Name: <input name="name" required><br>
        Email: <input type="email" name="email" required><br>
        Address: <input name="address" required><br>
        <button type="submit">Place Order</button>
    </form>
    """

@app.route('/admin')
def admin_dashboard():
    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    existing_categories = Category.query.all()
    if not existing_categories:
        default_cats = ["Rifle Accessories", "Pistol Accessories", "Outdoors Gear", "Misc."]
        db.session.add_all([Category(Name=name) for name in default_cats])
        db.session.commit()
        existing_categories = Category.query.all()
    form.category.choices = [(c.CategoryId, c.Name) for c in existing_categories]

    if form.validate_on_submit():
        product = Product(
            Name=form.name.data,
            Description=form.description.data,
            Price=form.price.data,
            Stock=form.stock.data,
            CategoryId=form.category.data
        )
        db.session.add(product)
        db.session.flush()  # To get ProductId before commit

        if form.image_url.data:
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
            ProductImage.query.filter_by(ProductId=product.ProductId, IsPrimary=True).update({'IsPrimary': False})
            existing_image = ProductImage.query.filter_by(ProductId=product.ProductId, ImageUrl=form.image_url.data).first()
            if existing_image:
                existing_image.IsPrimary = True
            else:
                db.session.add(ProductImage(ProductId=product.ProductId, ImageUrl=form.image_url.data, IsPrimary=True))

        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_dashboard'))

    existing_image = ProductImage.query.filter_by(ProductId=product.ProductId, IsPrimary=True).first()
    if existing_image:
        form.image_url.data = existing_image.ImageUrl

    return render_template('admin_edit_product.html', form=form, product=product)

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'danger')
    return redirect(url_for('admin_dashboard'))

# --- Cleanup function with logging and app context ---
def cleanup_duplicate_primary_images():
    with app.app_context():
        products_with_duplicates = (
            db.session.query(ProductImage.ProductId)
            .filter(ProductImage.IsPrimary == True)
            .group_by(ProductImage.ProductId)
            .having(db.func.count(ProductImage.ImageId) > 1)
            .all()
        )
        logger.info(f"Found {len(products_with_duplicates)} products with duplicate primary images.")

        for (product_id,) in products_with_duplicates:
            primary_images = (
                ProductImage.query.filter_by(ProductId=product_id, IsPrimary=True)
                .order_by(ProductImage.ImageId)
                .all()
            )
            for img in primary_images[1:]:
                img.IsPrimary = False
                logger.info(f"Demoted image {img.ImageId} of product {product_id} from primary.")

        db.session.commit()
        logger.info("Cleanup completed and committed.")

# --- Scheduler setup function ---
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_duplicate_primary_images, trigger='cron', hour=3, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    logger.info("Scheduler started with daily 3 AM cleanup job.")

# --- Main entry ---
if __name__ == '__main__':
    with app.app_context():
        start_scheduler()
        # Uncomment to run cleanup immediately at startup
        # cleanup_duplicate_primary_images()

    app.run(host='127.0.0.1', port=5000, debug=True)
