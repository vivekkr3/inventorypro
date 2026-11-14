"""
Inventory Management System
Flask application with full inventory, billing, supplier, customer,
analytics, and financial reporting capabilities.
"""
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, flash, request,
                   jsonify, abort)
from flask_login import (LoginManager, login_user, logout_user, login_required,
                         current_user)
from sqlalchemy import func, extract, desc

from config import Config
from models import (db, Store, User, Category, Product, Supplier, Customer,
                    Invoice, InvoiceItem, PurchaseOrder, PurchaseOrderItem, Expense,
                    init_master_database, init_store_database)
from forms import (LoginForm, RegisterForm, ProductForm, CategoryForm,
                   SupplierForm, CustomerForm, PurchaseOrderForm, ExpenseForm)
from flask_wtf.csrf import CSRFProtect
from flask.json.provider import DefaultJSONProvider

# ── App Factory ──────────────────────────────────────────────────────────────
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        return super().default(o)

app = Flask(__name__)
app.config.from_object(Config)
app.json = CustomJSONProvider(app)

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from flask import session
    store_id = session.get('store_id')
    if not store_id:
        return None
    return db.session.get(User, int(user_id))


@app.before_request
def before_request():
    from flask import session, g
    store_id = session.get('store_id')
    g.store_id = store_id
    if store_id:
        g.current_store = Store.query.filter_by(store_id=store_id, is_active=True).first()
    else:
        g.current_store = None


# ── Role Decorators ─────────────────────────────────────────────────────────
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(*roles):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ── Context Processor ────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    from flask import session, g
    store_id = session.get('store_id')
    current_store = getattr(g, 'current_store', None)
    all_stores = Store.query.filter_by(is_active=True).all()
    
    low_stock_count = 0
    if current_user.is_authenticated and store_id:
        try:
            low_stock_count = Product.query.filter(
                Product.is_active == True,
                Product.quantity <= Product.low_stock_threshold
            ).count()
        except Exception:
            low_stock_count = 0

    return dict(
        low_stock_count=low_stock_count,
        current_store_id=store_id or '',
        current_store_name=current_store.name if current_store else (store_id or ''),
        current_store_industry=current_store.industry if current_store else 'General Retail',
        current_store=current_store,
        all_stores=all_stores
    )


# ══════════════════════════════════════════════════════════════════════════════
#  BLUEPRINTS
# ══════════════════════════════════════════════════════════════════════════════
from flask import Blueprint

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
products_bp = Blueprint('products', __name__, url_prefix='/products')
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')
billing_bp = Blueprint('billing', __name__, url_prefix='/billing')
suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')
customers_bp = Blueprint('customers', __name__, url_prefix='/customers')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ── Main Routes ──────────────────────────────────────────────────────────────
@main_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


# ── Auth Routes (Multi-Tenant & Store-Aware) ─────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    all_stores = Store.query.filter_by(is_active=True).all()

    # Pre-fill store_id from query param if provided
    preset_store_id = request.args.get('store_id', '').strip().upper()
    if request.method == 'GET' and preset_store_id and not form.store_id.data:
        form.store_id.data = preset_store_id

    if form.validate_on_submit():
        store_id = form.store_id.data.strip().upper()
        store = Store.query.filter_by(store_id=store_id, is_active=True).first()
        
        if not store:
            flash(f"Store ID '{store_id}' was not found. Please verify the code or register a new store.", 'danger')
            return render_template('auth/login.html', form=form, all_stores=all_stores)

        # Route session to this tenant database
        from flask import session, g
        session['store_id'] = store_id
        session['store_name'] = store.name
        session['store_industry'] = store.industry
        g.store_id = store_id

        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data if hasattr(form, 'remember') else False)
            flash(f'Welcome back, {user.first_name}! Logged into {store.name} as {user.role.capitalize()}.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash(f"Invalid username or password for store '{store.name}' ({store_id}).", 'danger')

    return render_template('auth/login.html', form=form, all_stores=all_stores)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    all_stores = Store.query.filter_by(is_active=True).all()

    # Pre-fill store_id if passed in URL
    preset_store_id = request.args.get('store_id', '').strip().upper()
    if request.method == 'GET' and preset_store_id and not form.store_id.data:
        form.store_id.data = preset_store_id
        form.reg_type.data = 'join_store'

    if form.validate_on_submit():
        reg_type = request.form.get('reg_type', 'new_store')
        store_id = form.store_id.data.strip().upper()
        from flask import session, g

        if reg_type == 'new_store':
            # 1. Register a Brand New Store / Industry
            existing_store = Store.query.filter_by(store_id=store_id).first()
            if existing_store:
                flash(f"Store ID '{store_id}' is already taken. Please choose a different Store ID or join the existing store.", 'danger')
                return render_template('auth/register.html', form=form, all_stores=all_stores)

            store_name = form.store_name.data.strip() if form.store_name.data else f"Store {store_id}"
            industry = form.industry.data or 'General Retail'

            # Save store in master database
            new_store = Store(
                store_id=store_id,
                name=store_name,
                industry=industry,
                admin_email=form.email.data.strip().lower(),
                is_active=True
            )
            db.session.add(new_store)
            db.session.commit()

            # Initialize tenant tables in data/stores/{store_id}.db
            init_store_database(store_id)

            # Route context to the new store database
            session['store_id'] = store_id
            session['store_name'] = store_name
            session['store_industry'] = industry
            g.store_id = store_id

            # Create Root Admin User for this store
            admin_user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                role='admin',
                is_active_user=True
            )
            admin_user.set_password(form.password.data)
            db.session.add(admin_user)

            # Populate industry starter categories
            starter_categories = {
                'Consumer Electronics & IT': [
                    ("Laptops & Workstations", "Portable computers, ultrabooks, and workstations"),
                    ("Smartphones & Wearables", "Mobile phones, smartwatches, and chargers"),
                    ("Audio & Studio Acoustic", "Headphones, studio monitors, and wireless earbuds"),
                    ("Computer Peripherals", "Mechanical keyboards, mice, docks, and cables"),
                    ("Power & NVMe Storage", "External SSDs, flash drives, and high-wattage power banks")
                ],
                'Supermarket & Grocery': [
                    ("Fresh Farm Produce", "Organic vegetables and seasonal fruits"),
                    ("Dairy, Eggs & Bakery", "Artisanal breads, farm butter, and organic milk"),
                    ("Grains & Pantry Staples", "Basmati rice, whole wheat, and cold-pressed oils"),
                    ("Cold Beverages & Juices", "Natural fruit juices, kombucha, and craft coffee"),
                    ("Snacks & Health Foods", "Roasted nuts, seeds, and organic confectionery")
                ],
                'Fashion & Apparel': [
                    ("Men's Formal & Casual", "Shirts, denim, trousers, and blazers"),
                    ("Women's Collection", "Dresses, ethnic wear, tops, and footwear"),
                    ("Footwear & Accessories", "Sneakers, leather shoes, belts, and wallets"),
                    ("Seasonal Outerwear", "Jackets, hoodies, and winter accessories")
                ],
                'Pharmacy & Healthcare': [
                    ("Prescription Medicines", "Pharmaceutical therapeutics and standard medicines"),
                    ("OTC & First Aid Supplies", "Pain relief, fever care, and emergency kits"),
                    ("Vitamins & Daily Nutrition", "Multivitamins, omega-3, and protein supplements"),
                    ("Personal Care & Hygiene", "Skin care, oral hygiene, and sanitized supplies")
                ]
            }

            cats = starter_categories.get(industry, [
                ("General Merchandise", "Standard store merchandise items"),
                ("Fast Moving Consumer Goods", "High volume retail essentials"),
                ("Specialty Items", "Specialty and seasonal goods")
            ])
            for c_name, c_desc in cats:
                cat = Category(name=c_name, description=c_desc)
                db.session.add(cat)

            db.session.commit()

            # Automatically sign in the new store owner
            login_user(admin_user)
            flash(f"Store '{store_name}' ({store_id}) registered successfully! You are now logged in as Store Administrator.", "success")
            return redirect(url_for('dashboard.index'))

        else:
            # 2. Join an Existing Store as Staff (Manager or Cashier)
            store = Store.query.filter_by(store_id=store_id, is_active=True).first()
            if not store:
                flash(f"Store ID '{store_id}' does not exist. Please verify the Store Code from your store administrator.", 'danger')
                return render_template('auth/register.html', form=form, all_stores=all_stores)

            # Switch context to that store database
            session['store_id'] = store_id
            session['store_name'] = store.name
            session['store_industry'] = store.industry
            g.store_id = store_id

            if User.query.filter_by(username=form.username.data.strip()).first():
                flash(f"Username '{form.username.data}' already exists in store '{store.name}'. Please choose another username.", 'danger')
                return render_template('auth/register.html', form=form, all_stores=all_stores)

            if User.query.filter_by(email=form.email.data.strip().lower()).first():
                flash(f"Email '{form.email.data}' is already registered in store '{store.name}'.", 'danger')
                return render_template('auth/register.html', form=form, all_stores=all_stores)

            assigned_role = form.role.data if form.role.data in ['manager', 'cashier'] else 'cashier'

            staff_user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                role=assigned_role,
                is_active_user=True
            )
            staff_user.set_password(form.password.data)
            db.session.add(staff_user)
            db.session.commit()

            flash(f"Staff account created successfully for store '{store.name}'! Please sign in with Store ID: {store_id}.", 'success')
            return redirect(url_for('auth.login', store_id=store_id))

    return render_template('auth/register.html', form=form, all_stores=all_stores)


@auth_bp.route('/logout')
@login_required
def logout():
    from flask import session
    store_name = session.get('store_name', '')
    logout_user()
    session.pop('store_id', None)
    session.pop('store_name', None)
    session.pop('store_industry', None)
    flash(f'You have been safely signed out from {store_name}.' if store_name else 'You have been safely signed out.', 'info')
    return redirect(url_for('auth.login'))


# ── Dashboard ────────────────────────────────────────────────────────────────
@dashboard_bp.route('/')
@login_required
def index():
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    today_start = datetime.combine(today, datetime.min.time())

    total_products = Product.query.filter_by(is_active=True).count()
    low_stock = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= Product.low_stock_threshold
    ).all()

    today_sales = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.created_at >= today_start,
        Invoice.status == 'completed'
    ).scalar()

    monthly_revenue = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.created_at >= datetime.combine(month_start, datetime.min.time()),
        Invoice.status == 'completed'
    ).scalar()

    recent_invoices = Invoice.query.order_by(desc(Invoice.created_at)).limit(10).all()

    # 7-Day sales flow & invoice counts for the dynamic velocity chart
    chart_days = []
    chart_dates = []
    chart_sales = []
    chart_invoices = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_days.append(day.strftime('%a'))
        chart_dates.append(day.strftime('%a, %b %d') + (' (Today)' if i == 0 else ''))

        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())

        day_revenue = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            Invoice.status == 'completed',
            Invoice.created_at >= day_start,
            Invoice.created_at < day_end
        ).scalar()

        day_count = db.session.query(func.count(Invoice.id)).filter(
            Invoice.status == 'completed',
            Invoice.created_at >= day_start,
            Invoice.created_at < day_end
        ).scalar()

        chart_sales.append(round(float(day_revenue), 2))
        chart_invoices.append(int(day_count))

    has_sales_data = any(s > 0 for s in chart_sales) or any(c > 0 for c in chart_invoices)
    total_7d_sales = sum(chart_sales)
    total_7d_invoices = sum(chart_invoices)

    return render_template('dashboard.html',
                           total_products=total_products,
                           low_stock_items=low_stock,
                           today_sales=today_sales,
                           monthly_revenue=monthly_revenue,
                           recent_invoices=recent_invoices,
                           chart_days=chart_days,
                           chart_dates=chart_dates,
                           chart_sales=chart_sales,
                           chart_invoices=chart_invoices,
                           has_sales_data=has_sales_data,
                           total_7d_sales=total_7d_sales,
                           total_7d_invoices=total_7d_invoices)


# ── Products ─────────────────────────────────────────────────────────────────
@products_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', 0, type=int)

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) | (Product.sku.ilike(f'%{search}%'))
        )
    if category_filter:
        query = query.filter_by(category_id=category_filter)

    products = query.order_by(Product.name).paginate(page=page, per_page=15, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template('products/list.html',
                           products=products,
                           categories=categories,
                           search=search,
                           category_filter=category_filter)


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    form.supplier_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name).all()]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            sku=form.sku.data,
            description=form.description.data,
            category_id=form.category_id.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            cost_price=form.cost_price.data,
            selling_price=form.selling_price.data,
            quantity=form.quantity.data,
            low_stock_threshold=form.low_stock_threshold.data or 10,
            unit=form.unit.data or 'pcs'
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" added successfully!', 'success')
        return redirect(url_for('products.list'))

    return render_template('products/add.html', form=form)


@products_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    form.supplier_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name).all()]

    if form.validate_on_submit():
        product.name = form.name.data
        product.sku = form.sku.data
        product.description = form.description.data
        product.category_id = form.category_id.data
        product.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        product.cost_price = form.cost_price.data
        product.selling_price = form.selling_price.data
        product.quantity = form.quantity.data
        product.low_stock_threshold = form.low_stock_threshold.data
        product.unit = form.unit.data
        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('products.list'))

    if not form.supplier_id.data:
        form.supplier_id.data = 0
    return render_template('products/edit.html', form=form, product=product)


@products_bp.route('/delete/<int:id>')
@login_required
@role_required('admin', 'manager')
def delete(id):
    product = Product.query.get_or_404(id)
    product.is_active = False
    db.session.commit()
    flash(f'Product "{product.name}" deleted.', 'warning')
    return redirect(url_for('products.list'))


@products_bp.route('/add-category', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def add_category():
    name = request.form.get('category_name', '').strip()
    desc = request.form.get('category_description', '').strip()
    if name:
        if not Category.query.filter_by(name=name).first():
            cat = Category(name=name, description=desc)
            db.session.add(cat)
            db.session.commit()
            flash(f'Category "{name}" added.', 'success')
        else:
            flash('Category already exists.', 'warning')
    return redirect(url_for('products.list'))


# ── Inventory ────────────────────────────────────────────────────────────────
@inventory_bp.route('/')
@login_required
def list():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    total_value = sum(p.stock_value for p in products)
    low_stock_count = sum(1 for p in products if p.is_low_stock and p.quantity > 0)
    out_of_stock_count = sum(1 for p in products if p.quantity == 0)

    return render_template('inventory/list.html',
                           products=products,
                           total_value=total_value,
                           low_stock_count=low_stock_count,
                           out_of_stock_count=out_of_stock_count)


@inventory_bp.route('/alerts')
@login_required
def alerts():
    low_stock_products = Product.query.filter(
        Product.is_active == True,
        Product.quantity <= Product.low_stock_threshold
    ).order_by(Product.quantity).all()

    return render_template('inventory/alerts.html',
                           low_stock_products=low_stock_products)


# ── Billing ──────────────────────────────────────────────────────────────────
@billing_bp.route('/new')
@login_required
def new():
    products = Product.query.filter(
        Product.is_active == True, Product.quantity > 0
    ).order_by(Product.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('billing/new.html', products=products, customers=customers)


@billing_bp.route('/create', methods=['POST'])
@csrf.exempt
@login_required
def create_invoice():
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return jsonify({'error': 'No items provided', 'message': 'No items provided'}), 400

        # Generate invoice number
        inv_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Customer
        customer_id = data.get('customer_id')
        new_cust = data.get('new_customer')
        if new_cust and isinstance(new_cust, dict) and new_cust.get('name'):
            customer = Customer(
                name=new_cust.get('name'),
                email=new_cust.get('email', ''),
                phone=new_cust.get('phone', '')
            )
            db.session.add(customer)
            db.session.flush()
            customer_id = customer.id
        elif customer_id == 'new':
            customer_name = data.get('customer_name', 'Walk-in Customer')
            customer = Customer(name=customer_name, phone=data.get('customer_phone', ''))
            db.session.add(customer)
            db.session.flush()
            customer_id = customer.id
        elif customer_id:
            try:
                customer_id = int(customer_id)
            except (ValueError, TypeError):
                customer_id = None
        else:
            customer_id = None

        # Create invoice
        subtotal = 0
        invoice = Invoice(
            invoice_number=inv_number,
            customer_id=customer_id,
            user_id=current_user.id,
            tax_rate=float(data.get('tax_rate', 0)),
            discount=float(data.get('discount', 0)),
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes', '')
        )
        db.session.add(invoice)
        db.session.flush()

        # Add items
        for item_data in data['items']:
            product = Product.query.get(int(item_data['product_id']))
            if not product:
                return jsonify({'error': f'Product not found'}), 400

            qty = int(item_data['quantity'])
            if qty > product.quantity:
                return jsonify({'error': f'Insufficient stock for {product.name}. Available: {product.quantity}'}), 400

            unit_price = float(item_data.get('unit_price', product.selling_price))
            total_price = qty * unit_price

            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price
            )
            db.session.add(invoice_item)

            # Update inventory
            product.quantity -= qty
            subtotal += total_price

        # Calculate totals
        invoice.subtotal = subtotal
        invoice.tax_amount = subtotal * (invoice.tax_rate / 100)
        invoice.total_amount = subtotal + invoice.tax_amount - invoice.discount

        db.session.commit()
        return jsonify({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': inv_number,
            'redirect': url_for('billing.invoice', id=invoice.id)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    invoices = Invoice.query.order_by(desc(Invoice.created_at)).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('billing/list.html', invoices=invoices)


@billing_bp.route('/invoice/<int:id>')
@login_required
def invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('billing/invoice.html', invoice=invoice)


# ── Suppliers ────────────────────────────────────────────────────────────────
@suppliers_bp.route('/')
@login_required
def list():
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('suppliers/list.html', suppliers=suppliers)


@suppliers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'Supplier "{supplier.name}" added successfully!', 'success')
        return redirect(url_for('suppliers.list'))
    return render_template('suppliers/add.html', form=form)


@suppliers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    form = SupplierForm(obj=supplier)
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.email = form.email.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        supplier.city = form.city.data
        db.session.commit()
        flash(f'Supplier "{supplier.name}" updated.', 'success')
        return redirect(url_for('suppliers.list'))
    return render_template('suppliers/add.html', form=form, supplier=supplier)


@suppliers_bp.route('/delete/<int:id>')
@login_required
@role_required('admin')
def delete(id):
    supplier = Supplier.query.get_or_404(id)
    supplier.is_active = False
    db.session.commit()
    flash(f'Supplier "{supplier.name}" removed.', 'warning')
    return redirect(url_for('suppliers.list'))


@suppliers_bp.route('/purchase-orders')
@login_required
def purchase_orders():
    orders = PurchaseOrder.query.order_by(desc(PurchaseOrder.created_at)).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    return render_template('suppliers/purchase_orders.html',
                           purchase_orders=orders,
                           suppliers=suppliers,
                           products=products)


@suppliers_bp.route('/create-po', methods=['POST'])
@csrf.exempt
@login_required
@role_required('admin', 'manager')
def create_po():
    try:
        is_json = request.is_json
        data = request.get_json() if is_json else None

        supplier_id = None
        expected_delivery = None
        notes = ''
        items = []

        if is_json and data:
            supplier_id = int(data.get('supplier_id'))
            if data.get('expected_delivery'):
                expected_delivery = datetime.strptime(data['expected_delivery'], '%Y-%m-%d')
            notes = data.get('notes', '')
            items = data.get('items', [])
        else:
            supplier_id = int(request.form.get('supplier_id'))
            delivery_val = request.form.get('expected_delivery')
            if delivery_val:
                expected_delivery = datetime.strptime(delivery_val, '%Y-%m-%d')
            notes = request.form.get('notes', '')

            import re
            item_map = {}
            for key, val in request.form.items():
                m = re.match(r'po_items\[(\d+)\]\[(\w+)\]', key)
                if m:
                    idx, field = m.groups()
                    if idx not in item_map:
                        item_map[idx] = {}
                    item_map[idx][field] = val

            for idx, idata in item_map.items():
                if idata.get('product_id') and idata.get('quantity'):
                    items.append({
                        'product_id': int(idata['product_id']),
                        'quantity': int(idata['quantity']),
                        'unit_cost': float(idata.get('cost_price', 0))
                    })

        po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            user_id=current_user.id,
            expected_delivery=expected_delivery,
            notes=notes
        )
        db.session.add(po)
        db.session.flush()

        total = 0
        for item_data in items:
            qty = int(item_data['quantity'])
            unit_cost = float(item_data.get('unit_cost', 0))
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=int(item_data['product_id']),
                quantity=qty,
                unit_cost=unit_cost,
                total_cost=qty * unit_cost
            )
            db.session.add(item)
            total += item.total_cost

        po.total_amount = total
        db.session.commit()
        flash(f'Purchase Order {po_number} created successfully!', 'success')
        if is_json:
            return jsonify({'success': True, 'redirect': url_for('suppliers.purchase_orders')})
        return redirect(url_for('suppliers.purchase_orders'))
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error creating purchase order: {str(e)}', 'danger')
        return redirect(url_for('suppliers.purchase_orders'))


@suppliers_bp.route('/po/<int:id>')
@login_required
def view_po(id):
    po = PurchaseOrder.query.get_or_404(id)
    return render_template('suppliers/po_detail.html', po=po)


@suppliers_bp.route('/po-status/<int:id>', methods=['GET', 'POST'])
@suppliers_bp.route('/po-status/<int:id>/<status>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def update_po_status(id, status=None):
    po = PurchaseOrder.query.get_or_404(id)
    if not status:
        status = request.form.get('status') or request.args.get('status')

    valid = ['pending', 'ordered', 'delivered', 'cancelled']
    if not status or status not in valid:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('suppliers.purchase_orders'))

    po.status = status
    if status == 'delivered':
        po.delivered_at = datetime.utcnow()
        # Auto-add stock to products
        for item in po.items:
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity

    db.session.commit()
    flash(f'Purchase Order {po.po_number} marked as {status.capitalize()}.', 'success')
    return redirect(url_for('suppliers.purchase_orders'))


# ── Customers ────────────────────────────────────────────────────────────────
@customers_bp.route('/')
@login_required
def list():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)


@customers_bp.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    if name:
        customer = Customer(
            name=name,
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            address=request.form.get('address', '')
        )
        db.session.add(customer)
        db.session.commit()
        flash(f'Customer "{name}" added.', 'success')
    return redirect(url_for('customers.list'))


@customers_bp.route('/<int:id>')
@login_required
def detail(id):
    customer = Customer.query.get_or_404(id)
    return render_template('customers/detail.html', customer=customer)


@customers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form.get('name', '').strip()
        customer.email = request.form.get('email', '').strip()
        customer.phone = request.form.get('phone', '').strip()
        customer.address = request.form.get('address', '').strip()
        db.session.commit()
        flash(f'Customer "{customer.name}" updated successfully.', 'success')
        return redirect(url_for('customers.list'))
    return render_template('customers/edit.html', customer=customer)


@customers_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def delete(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer "{customer.name}" deleted.', 'warning')
    return redirect(url_for('customers.list'))


# ── Analytics ────────────────────────────────────────────────────────────────
@analytics_bp.route('/')
@login_required
def sales():
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    def sales_in_range(start, end=None):
        q = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            Invoice.status == 'completed',
            Invoice.created_at >= datetime.combine(start, datetime.min.time())
        )
        if end:
            q = q.filter(Invoice.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time()))
        return q.scalar()

    today_sales = sales_in_range(today, today)
    week_sales = sales_in_range(week_start, today)
    month_sales = sales_in_range(month_start, today)
    year_sales = sales_in_range(year_start)

    # Daily sales for chart (last 30 days)
    daily_sales = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        amount = sales_in_range(d, d)
        daily_sales.append({'date': d.strftime('%b %d'), 'amount': float(amount)})

    # Monthly revenue (last 12 months)
    monthly_revenue = []
    for i in range(11, -1, -1):
        m = today.replace(day=1) - timedelta(days=i * 30)
        m = m.replace(day=1)
        next_m = (m + timedelta(days=32)).replace(day=1)
        amount = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            Invoice.status == 'completed',
            Invoice.created_at >= datetime.combine(m, datetime.min.time()),
            Invoice.created_at < datetime.combine(next_m, datetime.min.time())
        ).scalar()
        monthly_revenue.append({'month': m.strftime('%b %Y'), 'amount': float(amount)})

    # Top selling products
    top_products = db.session.query(
        Product.name,
        func.sum(InvoiceItem.quantity).label('total_qty'),
        func.sum(InvoiceItem.total_price).label('total_revenue')
    ).join(InvoiceItem).join(Invoice).filter(
        Invoice.status == 'completed'
    ).group_by(Product.id).order_by(desc('total_qty')).limit(10).all()

    top_products_data = [{'name': p.name, 'qty': int(p.total_qty), 'revenue': float(p.total_revenue)} for p in top_products]

    return render_template('analytics/sales.html',
                           today_sales=today_sales,
                           week_sales=week_sales,
                           month_sales=month_sales,
                           year_sales=year_sales,
                           daily_sales_data=daily_sales,
                           monthly_revenue_data=monthly_revenue,
                           top_products_data=top_products_data)


# ── Reports ──────────────────────────────────────────────────────────────────
@reports_bp.route('/')
@login_required
@role_required('admin', 'manager')
def financial():
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)

    total_revenue = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.status == 'completed',
        Invoice.created_at >= datetime.combine(month_start, datetime.min.time())
    ).scalar()

    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.date >= datetime.combine(month_start, datetime.min.time())
    ).scalar()

    # COGS from invoices
    cogs = db.session.query(func.coalesce(func.sum(
        InvoiceItem.quantity * Product.cost_price
    ), 0)).join(Product).join(Invoice).filter(
        Invoice.status == 'completed',
        Invoice.created_at >= datetime.combine(month_start, datetime.min.time())
    ).scalar()

    total_expenses_all = float(total_expenses) + float(cogs)
    net_profit = float(total_revenue) - total_expenses_all
    profit_margin = (net_profit / float(total_revenue) * 100) if float(total_revenue) > 0 else 0

    expenses = Expense.query.order_by(desc(Expense.date)).limit(20).all()

    # Revenue by category
    revenue_by_cat = db.session.query(
        Category.name,
        func.sum(InvoiceItem.total_price)
    ).join(Product, Product.category_id == Category.id
    ).join(InvoiceItem, InvoiceItem.product_id == Product.id
    ).join(Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(Invoice.status == 'completed',
             Invoice.created_at >= datetime.combine(month_start, datetime.min.time())
    ).group_by(Category.name).all()

    revenue_data = [{'category': r[0], 'amount': float(r[1])} for r in revenue_by_cat]

    # Expense by category
    expense_by_cat = db.session.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.date >= datetime.combine(month_start, datetime.min.time())
    ).group_by(Expense.category).all()

    expense_data = [{'category': e[0], 'amount': float(e[1])} for e in expense_by_cat]

    expense_form = ExpenseForm()

    return render_template('reports/financial.html',
                           total_revenue=total_revenue,
                           total_expenses=total_expenses_all,
                           net_profit=net_profit,
                           profit_margin=profit_margin,
                           expenses=expenses,
                           revenue_data=revenue_data,
                           expense_data=expense_data,
                           expense_form=expense_form)


@reports_bp.route('/add-expense', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            description=form.description.data,
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data or datetime.utcnow(),
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added.', 'success')
    return redirect(url_for('reports.financial'))


# ── Register Blueprints ─────────────────────────────────────────────────────
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(products_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(reports_bp)


# ── Error Handlers ───────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', error='Page not found'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('base.html', error='Access denied'), 403


# ── Init DB & Run ────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

    # Create default admin if none exists
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@inventory.com',
            first_name='System',
            last_name='Admin',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: username='admin', password='admin123'")


if __name__ == '__main__':
    app.run(debug=True, port=5000)
