from datetime import datetime
from db import db

class User(db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FullName = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    addresses = db.relationship('Address', back_populates='user', cascade="all, delete-orphan")
    orders = db.relationship('Order', back_populates='user', cascade="all, delete-orphan")
    cart = db.relationship('Cart', uselist=False, back_populates='user', cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = 'Categories'
    CategoryId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)

    products = db.relationship('Product', back_populates='category', cascade="all, delete-orphan")


class Product(db.Model):
    __tablename__ = 'Products'
    ProductId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(150), nullable=False)
    Description = db.Column(db.Text)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    Stock = db.Column(db.Integer, nullable=False)
    CategoryId = db.Column(db.Integer, db.ForeignKey('Categories.CategoryId'))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', back_populates='products')
    images = db.relationship('ProductImage', back_populates='product', cascade="all, delete-orphan")
    order_items = db.relationship('OrderItem', back_populates='product', cascade="all, delete-orphan")
    cart_items = db.relationship('CartItem', back_populates='product', cascade="all, delete-orphan")

    def main_image(self):
        primary_img = next((img for img in self.images if img.IsPrimary), None)
        if primary_img:
            return primary_img.ImageUrl
        elif self.images:
            return self.images[0].ImageUrl
        else:
            return "default.jpg"  # fallback image

    @property
    def main_image_url(self):
        return self.main_image()


class ProductImage(db.Model):
    __tablename__ = 'ProductImages'
    ImageId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProductId = db.Column(db.Integer, db.ForeignKey('Products.ProductId'), nullable=False)
    ImageUrl = db.Column(db.String(255), nullable=False)
    IsPrimary = db.Column(db.Boolean, default=False)

    product = db.relationship('Product', back_populates='images')


class Address(db.Model):
    __tablename__ = 'Addresses'
    AddressId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    AddressLine1 = db.Column(db.String(200))
    AddressLine2 = db.Column(db.String(200))
    City = db.Column(db.String(100))
    State = db.Column(db.String(100))
    ZipCode = db.Column(db.String(20))
    Country = db.Column(db.String(100))
    IsDefault = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='addresses')
    orders = db.relationship('Order', back_populates='address')


class Order(db.Model):
    __tablename__ = 'Orders'
    OrderId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    AddressId = db.Column(db.Integer, db.ForeignKey('Addresses.AddressId'))
    TotalAmount = db.Column(db.Numeric(10, 2))
    Status = db.Column(db.String(50), default='Pending')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='orders')
    address = db.relationship('Address', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = 'OrderItems'
    OrderItemId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrderId = db.Column(db.Integer, db.ForeignKey('Orders.OrderId'), nullable=False)
    ProductId = db.Column(db.Integer, db.ForeignKey('Products.ProductId'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    UnitPrice = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')


class Cart(db.Model):
    __tablename__ = 'Cart'
    CartId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='cart')
    cart_items = db.relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")


class CartItem(db.Model):
    __tablename__ = 'CartItems'
    CartItemId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CartId = db.Column(db.Integer, db.ForeignKey('Cart.CartId'), nullable=False)
    ProductId = db.Column(db.Integer, db.ForeignKey('Products.ProductId'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)

    cart = db.relationship('Cart', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')
