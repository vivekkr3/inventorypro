import os
from datetime import datetime
from flask import session, g, has_request_context
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session as SignallingSession
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from config import Config

# Caches for database engines
master_engine = None
store_engines = {}


def get_master_engine():
    global master_engine
    if master_engine is None:
        master_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    return master_engine


def get_store_db_path(store_id):
    if not store_id:
        return Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    store_id = str(store_id).strip().upper()
    return os.path.join(Config.STORES_DIR, f"{store_id}.db")


def get_store_engine(store_id):
    if not store_id:
        return get_master_engine()
    store_id = str(store_id).strip().upper()
    if store_id not in store_engines:
        db_path = get_store_db_path(store_id)
        store_engines[store_id] = create_engine(f"sqlite:///{db_path}")
    return store_engines[store_id]


class MultiTenantRoutingSession(SignallingSession):
    """
    Dynamically routes SQLAlchemy queries to the appropriate database:
    - Queries for 'Store' route to master.db
    - Queries for tenant models route to data/stores/{store_id}.db based on session / request context
    """
    def get_bind(self, mapper=None, clause=None, **kw):
        if mapper and mapper.class_.__name__ == 'Store':
            return get_master_engine()

        # Check request-scoped g first, then session
        store_id = None
        if has_request_context():
            store_id = getattr(g, 'store_id', None)
            if not store_id and session:
                store_id = session.get('store_id')

        if store_id:
            return get_store_engine(store_id)
        return get_master_engine()


db = SQLAlchemy(session_options={'class_': MultiTenantRoutingSession})


# ═════════════════════════════════════════════════════════════════════════════
# 1. Master Database Models (Tenant Registry)
# ═════════════════════════════════════════════════════════════════════════════

class Store(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100), nullable=False, default='General Retail')
    admin_email = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'industry': self.industry,
            'admin_email': self.admin_email or '',
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }


# ═════════════════════════════════════════════════════════════════════════════
# 2. Store-Specific (Tenant) Models
# ═════════════════════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cashier')  # admin, manager, cashier
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_role(self, *roles):
        return self.role in roles


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    cost_price = db.Column(db.Float, nullable=False, default=0)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(20), default='pcs')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    invoice_items = db.relationship('InvoiceItem', backref='product', lazy=True)
    purchase_order_items = db.relationship('PurchaseOrderItem', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def stock_value(self):
        return self.quantity * self.cost_price

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'description': self.description or '',
            'cost_price': float(self.cost_price) if self.cost_price is not None else 0.0,
            'selling_price': float(self.selling_price) if self.selling_price is not None else 0.0,
            'quantity': self.quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'unit': self.unit or 'pcs',
            'category_id': self.category_id,
            'supplier_id': self.supplier_id
        }


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='supplier', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='customer', lazy=True)

    @property
    def total_purchases(self):
        return sum(inv.total_amount for inv in self.invoices)

    @property
    def last_purchase(self):
        if self.invoices:
            return max(inv.created_at for inv in self.invoices)
        return None


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subtotal = db.Column(db.Float, nullable=False, default=0)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    payment_method = db.Column(db.String(50), default='cash')
    status = db.Column(db.String(20), default='completed')  # completed, cancelled, refunded
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='invoices')

    @property
    def grand_total(self):
        return self.total_amount


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    @property
    def total(self):
        return self.total_price


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, ordered, delivered, cancelled
    expected_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='purchase_orders')

    @property
    def total(self):
        return self.total_amount


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

    @property
    def total(self):
        return self.total_cost


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(300), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='expenses')


# ═════════════════════════════════════════════════════════════════════════════
# 3. Database Initialization & Multi-Tenant Management Helpers
# ═════════════════════════════════════════════════════════════════════════════

def init_master_database():
    """Initializes the master registry database (stores table)."""
    engine = get_master_engine()
    Store.__table__.create(bind=engine, checkfirst=True)


def init_store_database(store_id):
    """Initializes all tenant tables inside data/stores/{store_id}.db"""
    engine = get_store_engine(store_id)
    tenant_tables = [
        User.__table__,
        Category.__table__,
        Supplier.__table__,
        Product.__table__,
        Customer.__table__,
        Invoice.__table__,
        InvoiceItem.__table__,
        PurchaseOrder.__table__,
        PurchaseOrderItem.__table__,
        Expense.__table__
    ]
    for table in tenant_tables:
        table.create(bind=engine, checkfirst=True)
