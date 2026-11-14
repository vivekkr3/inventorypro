# InventoryPro &mdash; Smart Inventory Management System

A full-stack, enterprise-grade Inventory Management System website built with **Python (Flask)**, **SQLAlchemy**, **SQLite**, and **Bootstrap 5.3**. Designed for retail businesses such as grocery stores, stationery shops, electronics outlets, and departmental stores.

---

## 🌟 Key Features

### 1. 💼 Professional Landing Page
- High-converting, modern SaaS landing page.
- Hero banner with animations, feature showcases, workflow steps, live statistics counter, customer testimonials, and quick access to authentication.

### 2. 📦 Product Management
- Full CRUD operations: Product name, SKU, category, cost price, selling price, quantity, low-stock threshold, and unit of measurement.
- Real-time category creation and product category filtering.
- Instant search by product name or SKU.
- Soft-deletion ensuring historical sales and invoice integrity.

### 3. 📊 Inventory Management & Stock Tracking
- Real-time stock level monitoring with status indicators:
  - 🟢 **In Stock**
  - 🟡 **Low Stock** (threshold-based)
  - 🔴 **Out of Stock**
- Dynamic inventory valuation (Total Stock Value, Units Count).
- Direct restocking workflow via Purchase Orders.

### 4. 🧾 Billing & Point of Sale (POS)
- Fast invoice builder with dynamic line items (add/remove rows, product selection, auto-filled prices).
- Real-time calculations: Subtotal, customizable tax percentage, discount deductions, and Grand Total.
- **Automatic Inventory Deduction**: Stock automatically decrements in real-time upon successful billing.
- Walk-in or saved customer support with inline quick-add.
- Printable, professional invoice layouts (`/billing/invoice/<id>`).

### 5. ⚠️ Low-Stock Alerts
- Automated detection of products where `quantity <= low_stock_threshold`.
- Top-navbar notification badge showing real-time low-stock count across the app.
- Dedicated alerts page (`/inventory/alerts`) with reorder recommendations.

### 6. 🚚 Supplier Management & Purchase Orders
- Supplier directory with contact details, email, phone, city, and address.
- Comprehensive Purchase Order (PO) creation with line items and cost pricing.
- PO lifecycle tracking: `Pending` &rarr; `Ordered` &rarr; `Delivered` &rarr; `Cancelled`.
- **Automatic Stock Replenishment**: Marking a purchase order as "Delivered" automatically increases product inventory.
- Printable Purchase Order view (`/suppliers/po/<id>`).

### 7. 👥 Customer Management
- Complete customer profiles and contact details.
- Comprehensive purchase history per customer with clickable links to all previous invoices.
- Total lifetime expenditure and last purchase date calculation.

### 8. 📈 Sales Analytics
- Interactive **Chart.js** visualizations:
  - **30-Day Daily Sales Trend** (Line Chart)
  - **12-Month Revenue History** (Bar Chart)
  - **Top 5 Best-Selling Products** (Doughnut Chart)
- Sales metric cards: Today's Sales, This Week, This Month, and This Year.
- Best-selling products ranked by units sold and generated revenue.

### 9. 💰 Financial Reporting & Expense Management
- Comprehensive financial statement calculations:
  - **Total Revenue** (from completed sales invoices)
  - **Cost of Goods Sold (COGS)**
  - **Operating Expenses** (rent, utilities, salaries, marketing, supplies)
  - **Net Profit & Profit Margin (%)**
- Categorized expense tracking with inline expense entry form.
- Visual revenue and expense distribution charts.

### 10. 🔒 Role-Based Access Control (RBAC)
- Three access tiers with secure password hashing:
  - **Admin**: Full system access (product creation/deletion, supplier management, financial reports, user management).
  - **Manager**: Products, inventory, billing, suppliers, purchase orders, and financial reports.
  - **Cashier**: Streamlined interface for billing, invoice generation, customer lookup, and stock checking (restricted from financial reports and deletion).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Installation
Open PowerShell or Terminal in the project root folder:
```powershell
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Pre-populates sample categories, 24 products, suppliers, customers, 70+ invoices, and expenses:
```powershell
python seed_data.py
```

### 4. Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Multi-Tenant Store Codes & Login Credentials

| Store Code | Store Name & Industry | Role | Username | Password |
|---|---|---|---|---|
| **`STORE001`** | **TechMart** (Consumer Electronics & IT) | **Admin** | `admin` | `admin123` |
| **`STORE001`** | **TechMart** (Consumer Electronics & IT) | **Manager** | `manager1` | `manager123` |
| **`STORE001`** | **TechMart** (Consumer Electronics & IT) | **Cashier** | `cashier1` | `cashier123` |
| **`GROCERY01`** | **GreenLeaf** (Supermarket & Organics) | **Admin** | `admin` | `admin123` |
| **`PHARMA01`** | **CarePlus** (Pharmacy & Healthcare) | **Admin** | `admin` | `admin123` |
| **`STORE1`** | **APEX1** (Supermarket & Grocery) | **Cashier** | `cashier1` | `cashier123` |

---

## ⚡ Power-User Keyboard Navigation (`Ctrl + K` & Chords)

- **Global Command Palette:** Press <kbd>Ctrl</kbd> + <kbd>K</kbd> (or <kbd>⌘K</kbd>) to search actions, jump between routes, or switch store databases with 1 click.
- **Two-Key Navigation Chords (Linear/Vim style):**
  - <kbd>G</kbd> then <kbd>B</kbd> &rarr; **Go to Billing** (New POS Invoice creation)
  - <kbd>G</kbd> then <kbd>D</kbd> &rarr; **Go to Dashboard**
  - <kbd>G</kbd> then <kbd>P</kbd> &rarr; **Go to Products**
  - <kbd>G</kbd> then <kbd>I</kbd> &rarr; **Go to Inventory**
  - <kbd>G</kbd> then <kbd>A</kbd> &rarr; **Go to Alerts**
  - <kbd>T</kbd> &rarr; **Toggle Dark / Light Theme**

---

## 📁 Project Architecture

```
semester_project/
├── app.py                     # Main application factory, blueprints & dynamic multi-tenant router
├── config.py                  # App configuration & settings
├── models.py                  # SQLAlchemy models & physical database-per-store routing
├── forms.py                   # Flask-WTF forms & CSRF validation
├── seed_data.py               # Master & tenant multi-store seeder
├── requirements.txt           # Python dependencies (Flask, ReportLab, etc.)
├── DOCUMENTATION.md           # Full official technical & API reference
├── data/
│   ├── master.db              # Central Master Store Registry (Store IDs, industries)
│   └── stores/                # Physical isolated SQLite databases per store
│       ├── STORE001.db        # TechMart database
│       ├── GROCERY01.db       # GreenLeaf Supermarket database
│       ├── PHARMA01.db        # CarePlus Pharmacy database
│       └── STORE1.db          # APEX1 database
├── static/
│   ├── css/style.css          # Design system, Command Palette, Spotlights, Sparklines
│   └── js/main.js             # Command palette, keyboard chords, mouse spotlights
├── templates/                 # Jinja2 templates (dashboard, products, billing, reports)
└── *.pdf                      # Academic reports & presentation viva guides
```
