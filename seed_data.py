"""
Multi-Store Multi-Tenant Seeder for InventoryPro.
Seeds multiple distinct stores with isolated databases in data/stores/{store_id}.db
and registers them in data/master.db.
"""
import os
import shutil
import random
from datetime import datetime, timedelta

from app import app
from models import (
    db, Store, User, Category, Product, Supplier, Customer,
    Invoice, InvoiceItem, PurchaseOrder, PurchaseOrderItem, Expense,
    init_master_database, init_store_database, get_store_engine
)
from config import Config


def seed_store_users(store_id):
    """Seed standard staff roles for the given store."""
    users_data = [
        ("admin", f"admin@{store_id.lower()}.com", "admin123", "admin", "Alex", "Vance"),
        ("manager1", f"manager@{store_id.lower()}.com", "manager123", "manager", "Marcus", "Reed"),
        ("cashier1", f"cashier@{store_id.lower()}.com", "cashier123", "cashier", "Chloe", "Bennett"),
    ]
    created = []
    for uname, email, pwd, role, fn, ln in users_data:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(
                username=uname,
                email=email,
                role=role,
                first_name=fn,
                last_name=ln,
                is_active_user=True
            )
            u.set_password(pwd)
            db.session.add(u)
            db.session.flush()
        created.append(u)
    db.session.commit()
    return created


def seed_store001_tech():
    """Seed Store 1: TechMart Electronics & IT Solutions."""
    print("-> Seeding STORE001 (TechMart Electronics)...")
    init_store_database('STORE001')

    with app.test_request_context():
        from flask import session
        session['store_id'] = 'STORE001'

        admin, mgr, cashier = seed_store_users('STORE001')

        # Categories
        cat_names = [
            ("Laptops & Computers", "Workstations, ultrabooks, and desktop accessories"),
            ("Smartphones & Tablets", "Mobile devices and cellular hardware"),
            ("Audio & Sound", "Headphones, wireless earbuds, and studio monitors"),
            ("Peripherals & Cables", "Keyboards, mice, USB-C docks, and HDMI cables"),
            ("Power & Storage", "High-capacity power banks, NVMe SSDs, and flash drives"),
            ("Smart Home & IoT", "Connected bulbs, smart plugs, and home automation"),
        ]
        categories = []
        for name, desc in cat_names:
            c = Category.query.filter_by(name=name).first()
            if not c:
                c = Category(name=name, description=desc)
                db.session.add(c)
                db.session.flush()
            categories.append(c)

        # Suppliers
        suppliers = []
        sup_data = [
            ("Apex Electronics Wholesale", "Sunil Mehta", "sales@apexelectronics.in", "+91 98200 11223", "Mumbai", "Andheri East Tech Zone"),
            ("Global Silicon Logistics", "Ananya Sen", "orders@globalsilicon.com", "+91 98300 44556", "Bangalore", "Electronic City Phase 1"),
            ("Zenith Audio Labs", "Karan Johar", "contact@zenithaudio.in", "+91 98400 77889", "Chennai", "Anna Salai Industrial Hub"),
            ("Metro Power & Cables", "Pooja Hegde", "metro@powercables.com", "+91 98100 99001", "Delhi", "Nehru Place IT Complex"),
        ]
        for name, cp, email, phone, city, addr in sup_data:
            s = Supplier.query.filter_by(name=name).first()
            if not s:
                s = Supplier(name=name, contact_person=cp, email=email, phone=phone, city=city, address=addr)
                db.session.add(s)
                db.session.flush()
            suppliers.append(s)

        # Products
        prod_specs = [
            ("MacBook Pro M3 14-inch", "TECH-MBP-01", 0, 145000, 169900, 12, 4, "pcs", 0),
            ("Dell XPS 15 OLED", "TECH-XPS-02", 0, 120000, 139900, 8, 3, "pcs", 0),
            ("Lenovo ThinkPad X1 Carbon", "TECH-TPX-03", 0, 95000, 115000, 15, 5, "pcs", 0),
            ("iPhone 15 Pro 256GB", "TECH-IP15-01", 1, 105000, 124900, 24, 6, "pcs", 1),
            ("Samsung Galaxy S24 Ultra", "TECH-S24U-02", 1, 98000, 119999, 18, 5, "pcs", 1),
            ("OnePlus 12 512GB", "TECH-OP12-03", 1, 54000, 64999, 30, 8, "pcs", 1),
            ("Sony WH-1000XM5 ANC", "TECH-SNY-01", 2, 22000, 28990, 25, 6, "pcs", 2),
            ("Bose QuietComfort Ultra", "TECH-BSE-02", 2, 26000, 32900, 14, 4, "pcs", 2),
            ("Apple AirPods Pro 2", "TECH-APP-03", 2, 17500, 22900, 40, 10, "pcs", 2),
            ("Logitech MX Master 3S", "TECH-MXM-01", 3, 6200, 8495, 45, 10, "pcs", 3),
            ("Keychron K2 Pro Wireless", "TECH-KEY-02", 3, 7500, 9999, 20, 5, "pcs", 3),
            ("Anker 10-in-1 USB-C Hub", "TECH-ANK-03", 3, 3800, 5499, 50, 12, "pcs", 3),
            ("Samsung T7 Shield 2TB SSD", "TECH-SSD-01", 4, 11500, 14999, 28, 6, "pcs", 0),
            ("Anker 24000mAh Power Bank", "TECH-PB-02", 4, 8500, 11499, 22, 5, "pcs", 3),
            ("Philips Hue Ambient Kit", "TECH-HUE-01", 5, 4500, 6999, 16, 4, "pcs", 2),
            ("Amazon Echo Show 8", "TECH-ECH-02", 5, 7000, 8999, 19, 5, "pcs", 1),
        ]
        products = []
        for name, sku, cat_idx, cost, sell, qty, thresh, unit, sup_idx in prod_specs:
            p = Product.query.filter_by(sku=sku).first()
            if not p:
                p = Product(
                    name=name, sku=sku, category_id=categories[cat_idx].id,
                    cost_price=cost, selling_price=sell, quantity=qty,
                    low_stock_threshold=thresh, unit=unit,
                    supplier_id=suppliers[sup_idx].id
                )
                db.session.add(p)
                db.session.flush()
            products.append(p)

        # Customers
        customers = []
        cust_data = [
            ("Aarav Mehta", "aarav.mehta@gmail.com", "+91 98211 22334", "Bandra West, Mumbai"),
            ("Diya Sen", "diya.sen@outlook.com", "+91 98322 33445", "Indiranagar, Bangalore"),
            ("Rohan Gupta", "rohan.g@yahoo.com", "+91 98433 44556", "Vasant Vihar, New Delhi"),
            ("Kavita Rao", "kavita.rao@techcorp.in", "+91 98544 55667", "Jubilee Hills, Hyderabad"),
        ]
        for name, email, phone, addr in cust_data:
            cust = Customer.query.filter_by(email=email).first()
            if not cust:
                cust = Customer(name=name, email=email, phone=phone, address=addr)
                db.session.add(cust)
                db.session.flush()
            customers.append(cust)

        # Seed realistic Invoices
        pay_methods = ['cash', 'upi', 'card', 'bank_transfer']
        for i in range(1, 26):
            inv_num = f"TECH-INV-{1000 + i}"
            if not Invoice.query.filter_by(invoice_number=inv_num).first():
                cust = random.choice(customers) if random.random() > 0.25 else None
                days_ago = random.randint(0, 45)
                inv_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(1, 10))
                
                selected_prods = random.sample(products, random.randint(1, 3))
                subtotal = 0
                items_to_add = []
                for p in selected_prods:
                    qty = random.randint(1, 2)
                    total_p = p.selling_price * qty
                    subtotal += total_p
                    items_to_add.append((p.id, qty, p.selling_price, total_p))

                tax_rate = 18.0
                tax_amt = subtotal * 0.18
                discount = 500 if subtotal > 15000 else 0
                grand_total = subtotal + tax_amt - discount

                inv = Invoice(
                    invoice_number=inv_num,
                    customer_id=cust.id if cust else None,
                    user_id=cashier.id,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amt,
                    discount=discount,
                    total_amount=grand_total,
                    payment_method=random.choice(pay_methods),
                    status='completed',
                    created_at=inv_date
                )
                db.session.add(inv)
                db.session.flush()

                for pid, qty, price, tot in items_to_add:
                    item = InvoiceItem(
                        invoice_id=inv.id,
                        product_id=pid,
                        quantity=qty,
                        unit_price=price,
                        total_price=tot
                    )
                    db.session.add(item)

        # Expenses
        expenses_data = [
            ("Tech Zone Commercial Showroom Lease", 45000, "rent", 25),
            ("High-Speed Fiber Internet & Cloud Backup", 4200, "utilities", 18),
            ("Store Electricity & Climate Control", 8500, "utilities", 10),
            ("Retail Staff Monthly Compensation", 65000, "salary", 5),
            ("Social Media & Google Ads Lead Generation", 12000, "marketing", 12),
        ]
        for desc, amt, cat, days in expenses_data:
            e = Expense.query.filter_by(description=desc).first()
            if not e:
                e = Expense(
                    description=desc, amount=amt, category=cat,
                    date=datetime.utcnow() - timedelta(days=days),
                    user_id=admin.id
                )
                db.session.add(e)

        db.session.commit()
    print("-> STORE001 seeded successfully!")


def seed_store002_grocery():
    """Seed Store 2: GreenLeaf Fresh Organics & Supermarket."""
    print("-> Seeding GROCERY01 (GreenLeaf Organics & Supermarket)...")
    init_store_database('GROCERY01')

    with app.test_request_context():
        from flask import session
        session['store_id'] = 'GROCERY01'

        admin, mgr, cashier = seed_store_users('GROCERY01')

        # Categories
        cat_names = [
            ("Fresh Produce & Organic", "Farm fresh vegetables, exotic fruits, and fresh herbs"),
            ("Dairy, Eggs & Bakery", "Artisanal breads, farm butter, cheese, and farm-fresh milk"),
            ("Pantry Staples & Grains", "Premium basmati rice, cold-pressed oils, organic pulses"),
            ("Beverages & Juices", "Cold-pressed juices, organic tea, kombucha, and craft coffee"),
            ("Healthy Snacks & Nuts", "Roasted nuts, trail mixes, dried cranberries, and seeds"),
            ("Eco Household & Care", "Biodegradable cleaners, bamboo paper, natural hygiene"),
        ]
        categories = []
        for name, desc in cat_names:
            c = Category.query.filter_by(name=name).first()
            if not c:
                c = Category(name=name, description=desc)
                db.session.add(c)
                db.session.flush()
            categories.append(c)

        # Suppliers
        suppliers = []
        sup_data = [
            ("Sahyadri Organic Cooperative", "Vikas Patil", "supply@sahyadriorganics.org", "+91 97600 12345", "Nashik", "Grape Valley Agri Hub"),
            ("Himalayan Pure Farms", "Simran Kaur", "simran@himalayanfarms.in", "+91 97700 23456", "Dehradun", "Valley Organic Estate"),
            ("Coastal Spice & Oil Mills", "Suresh Shenoy", "suresh@coastalspice.com", "+91 97800 34567", "Mangalore", "Bunder Port Road"),
            ("GreenEarth Eco Logistics", "Meera Nambiar", "orders@greenearth.in", "+91 97900 45678", "Kochi", "Kakkanad Export Park"),
        ]
        for name, cp, email, phone, city, addr in sup_data:
            s = Supplier.query.filter_by(name=name).first()
            if not s:
                s = Supplier(name=name, contact_person=cp, email=email, phone=phone, city=city, address=addr)
                db.session.add(s)
                db.session.flush()
            suppliers.append(s)

        # Products
        prod_specs = [
            ("Organic Hass Avocados (Pack of 2)", "GROC-AVO-01", 0, 180, 260, 45, 10, "pack", 0),
            ("Hydroponic Baby Spinach 250g", "GROC-SPN-02", 0, 45, 75, 60, 15, "box", 0),
            ("Fresh Blueberries 125g", "GROC-BER-03", 0, 190, 275, 30, 8, "punnet", 0),
            ("A2 Desi Cow Milk 1L Bottle", "GROC-MLK-01", 1, 65, 85, 80, 20, "bottle", 1),
            ("Artisanal Sourdough Bread Loaf", "GROC-BRD-02", 1, 95, 140, 25, 6, "loaf", 1),
            ("Himalayan Organic Ghee 500ml", "GROC-GHE-03", 1, 480, 650, 40, 10, "jar", 1),
            ("Royal Daawat Basmati Rice 5kg", "GROC-RIC-01", 2, 380, 520, 50, 12, "bag", 2),
            ("Cold-Pressed Extra Virgin Olive Oil 1L", "GROC-OIL-02", 2, 650, 890, 35, 8, "bottle", 2),
            ("Organic Quinoa Grain 1kg", "GROC-QNA-03", 2, 220, 310, 40, 10, "pack", 0),
            ("Matcha Ceremonial Grade Tea 100g", "GROC-MTC-01", 3, 520, 750, 22, 5, "tin", 1),
            ("Sparkling Passionfruit Kombucha 330ml", "GROC-KMB-02", 3, 85, 130, 60, 15, "bottle", 3),
            ("Artisan Dark Roasted Coffee Beans 500g", "GROC-COF-03", 3, 340, 480, 28, 6, "bag", 2),
            ("Raw California Almonds 500g", "GROC-ALM-01", 4, 380, 520, 50, 10, "pack", 0),
            ("Chia Seeds & Flax Mix 250g", "GROC-CHI-02", 4, 110, 175, 45, 10, "jar", 1),
            ("Biodegradable Bamboo Kitchen Towels", "GROC-ECO-01", 5, 140, 210, 35, 8, "roll", 3),
            ("Natural Plant-Based Dish Wash 500ml", "GROC-DW-02", 5, 120, 175, 40, 10, "bottle", 3),
        ]
        products = []
        for name, sku, cat_idx, cost, sell, qty, thresh, unit, sup_idx in prod_specs:
            p = Product.query.filter_by(sku=sku).first()
            if not p:
                p = Product(
                    name=name, sku=sku, category_id=categories[cat_idx].id,
                    cost_price=cost, selling_price=sell, quantity=qty,
                    low_stock_threshold=thresh, unit=unit,
                    supplier_id=suppliers[sup_idx].id
                )
                db.session.add(p)
                db.session.flush()
            products.append(p)

        # Customers
        customers = []
        cust_data = [
            ("Pooja Singhania", "pooja.singh@gmail.com", "+91 98111 22334", "Koregaon Park, Pune"),
            ("Dr. Arvind Swaminathan", "arvind.doc@aiims.edu", "+91 98222 33445", "Beshant Nagar, Chennai"),
            ("Sanjana Kapur", "sanjana@kapurfashion.com", "+91 98333 44556", "Vasant Kunj, New Delhi"),
        ]
        for name, email, phone, addr in cust_data:
            cust = Customer.query.filter_by(email=email).first()
            if not cust:
                cust = Customer(name=name, email=email, phone=phone, address=addr)
                db.session.add(cust)
                db.session.flush()
            customers.append(cust)

        # Invoices
        pay_methods = ['cash', 'upi', 'card']
        for i in range(1, 20):
            inv_num = f"GROC-INV-{2000 + i}"
            if not Invoice.query.filter_by(invoice_number=inv_num).first():
                cust = random.choice(customers) if random.random() > 0.3 else None
                days_ago = random.randint(0, 30)
                inv_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(1, 12))
                
                selected_prods = random.sample(products, random.randint(2, 4))
                subtotal = 0
                items_to_add = []
                for p in selected_prods:
                    qty = random.randint(1, 4)
                    tot = p.selling_price * qty
                    subtotal += tot
                    items_to_add.append((p.id, qty, p.selling_price, tot))

                tax_rate = 5.0  # Food tax
                tax_amt = subtotal * 0.05
                discount = 50 if subtotal > 1000 else 0
                grand_total = subtotal + tax_amt - discount

                inv = Invoice(
                    invoice_number=inv_num,
                    customer_id=cust.id if cust else None,
                    user_id=cashier.id,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amt,
                    discount=discount,
                    total_amount=grand_total,
                    payment_method=random.choice(pay_methods),
                    status='completed',
                    created_at=inv_date
                )
                db.session.add(inv)
                db.session.flush()

                for pid, qty, price, tot in items_to_add:
                    item = InvoiceItem(
                        invoice_id=inv.id,
                        product_id=pid,
                        quantity=qty,
                        unit_price=price,
                        total_price=tot
                    )
                    db.session.add(item)

        # Expenses
        expenses_data = [
            ("Cold Storage & Refrigeration Power", 14500, "utilities", 15),
            ("Eco Kraft Paper Bags & Packaging", 3200, "supplies", 8),
            ("Store Prime Space Rent", 32000, "rent", 28),
            ("Local Organic Farmers Market Stall", 5000, "marketing", 12),
        ]
        for desc, amt, cat, days in expenses_data:
            e = Expense.query.filter_by(description=desc).first()
            if not e:
                e = Expense(
                    description=desc, amount=amt, category=cat,
                    date=datetime.utcnow() - timedelta(days=days),
                    user_id=admin.id
                )
                db.session.add(e)

        db.session.commit()
    print("-> GROCERY01 seeded successfully!")


def seed_store003_pharma():
    """Seed Store 3: CarePlus Pharmacy & Wellness."""
    print("-> Seeding PHARMA01 (CarePlus Pharmacy)...")
    init_store_database('PHARMA01')

    with app.test_request_context():
        from flask import session
        session['store_id'] = 'PHARMA01'

        admin, mgr, cashier = seed_store_users('PHARMA01')

        # Categories
        cat_names = [
            ("Prescription Medicines", "Standard pharmaceuticals & therapeutics"),
            ("OTC & Pain Relief", "Over-the-counter remedies and antipyretics"),
            ("Vitamins & Supplements", "Multivitamins, omega-3, and protein nutrition"),
            ("First Aid & Surgical", "Bandages, antiseptics, digital thermometers, and gauze"),
        ]
        categories = []
        for name, desc in cat_names:
            c = Category.query.filter_by(name=name).first()
            if not c:
                c = Category(name=name, description=desc)
                db.session.add(c)
                db.session.flush()
            categories.append(c)

        # Suppliers
        s1 = Supplier(name="Cipla Lifecare Distributors", contact_person="Ramesh Gupta", email="care@cipladist.in", phone="+91 99000 11223", city="Mumbai", address="MIDC Industrial Area")
        s2 = Supplier(name="Apollo Surgical Supplies", contact_person="Deepak Verma", email="apollo@surgicals.com", phone="+91 99000 22334", city="Hyderabad", address="Genome Valley")
        db.session.add_all([s1, s2])
        db.session.flush()

        # Products
        prod_specs = [
            ("Paracetamol 650mg (Strip of 15)", "PHAR-PCM-01", 1, 18, 32, 120, 25, "strip", s1.id),
            ("Digital Infrared Thermometer", "PHAR-THM-02", 3, 650, 999, 25, 5, "pcs", s2.id),
            ("Omega-3 Fish Oil 1000mg (60 Caps)", "PHAR-OMG-03", 2, 420, 699, 40, 8, "bottle", s1.id),
            ("Antiseptic Liquid 500ml", "PHAR-ANT-04", 3, 110, 165, 50, 10, "bottle", s2.id),
            ("Vitamin C + Zinc Chewables (60 Tabs)", "PHAR-VTC-05", 2, 140, 230, 80, 15, "bottle", s1.id),
        ]
        for name, sku, cat_idx, cost, sell, qty, thresh, unit, sup_id in prod_specs:
            p = Product(
                name=name, sku=sku, category_id=categories[cat_idx].id,
                cost_price=cost, selling_price=sell, quantity=qty,
                low_stock_threshold=thresh, unit=unit, supplier_id=sup_id
            )
            db.session.add(p)

        db.session.commit()
    print("-> PHARMA01 seeded successfully!")


def seed_all():
    """Initializes master database registry and seeds all demo stores."""
    print("=" * 60)
    print("Initializing Master Store Registry & Multi-Tenant Databases...")
    print("=" * 60)

    with app.app_context():
        init_master_database()

        # 1. Register Stores in master.db
        stores_to_register = [
            ('STORE001', 'TechMart Electronics & IT Hub', 'Consumer Electronics & IT', 'admin@store001.com'),
            ('GROCERY01', 'GreenLeaf Fresh Organics & Supermarket', 'Supermarket & Grocery', 'admin@grocery01.com'),
            ('PHARMA01', 'CarePlus Pharmacy & Healthcare', 'Pharmacy & Healthcare', 'admin@pharma01.com'),
        ]

        for sid, sname, sindustry, email in stores_to_register:
            store = Store.query.filter_by(store_id=sid).first()
            if not store:
                store = Store(
                    store_id=sid,
                    name=sname,
                    industry=sindustry,
                    admin_email=email,
                    is_active=True
                )
                db.session.add(store)
                db.session.flush()
        db.session.commit()
        print("[OK] Master Store Registry initialized with 3 demo stores.")

    # 2. Seed each store's isolated database
    seed_store001_tech()
    seed_store002_grocery()
    seed_store003_pharma()

    print("=" * 60)
    print("Multi-Store Multi-Tenant Seeding Complete!")
    print("Demo Stores Ready:")
    print(" 1. STORE001  -> TechMart Electronics & IT Hub")
    print(" 2. GROCERY01 -> GreenLeaf Fresh Organics & Supermarket")
    print(" 3. PHARMA01  -> CarePlus Pharmacy & Healthcare")
    print("=" * 60)


if __name__ == '__main__':
    seed_all()
