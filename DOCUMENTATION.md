# InventoryPro &bull; Official System Documentation & Architectural Specification

> **Platform Version:** 2.5 Enterprise  
> **Architecture Pattern:** Multi-Tenant Database-per-Store with Dynamic Scoped Session Routing  
> **Tech Stack:** Python 3.13, Flask 3.0, Flask-SQLAlchemy 2.0, SQLite (WAL Mode), Bootstrap 5.3, Chart.js 4, ReportLab  

---

## 📑 Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Multi-Tenant Database Engine](#2-multi-tenant-database-engine)
3. [Relational Schema & Data Dictionary](#3-relational-schema--data-dictionary)
4. [Role-Based Access Control (RBAC)](#4-role-based-access-control-rbac)
5. [Core Functional Modules & Business Engines](#5-core-functional-modules--business-engines)
   - [Real-Time Point-of-Sale (POS) & Thermal Invoicing](#51-real-time-point-of-sale-pos--thermal-invoicing)
   - [Automated Safety Stock Sentinel & Alerts](#52-automated-safety-stock-sentinel--alerts)
   - [Procurement & Closed-Loop Purchase Orders](#53-procurement--closed-loop-purchase-orders)
   - [GAAP Financial Cost Accounting & P&L Engine](#54-gaap-financial-cost-accounting--pl-engine)
6. [Complete Route & Endpoint Reference](#6-complete-route--endpoint-reference)
7. [Elite SaaS Frontend UX & Keyboard Interaction Engine](#7-elite-saas-frontend-ux--keyboard-interaction-engine)
8. [Security Governance & Threat Defense Model](#8-security-governance--threat-defense-model)
9. [Installation, Seeding & Production Deployment Guide](#9-installation-seeding--production-deployment-guide)
10. [Automated Verification Test Suites](#10-automated-verification-test-suites)

---

## 1. System Overview & Architecture

**InventoryPro** is an enterprise-grade multi-tenant software-as-a-service (SaaS) platform engineered for retail chains, pharmacies, electronics distributors, supermarkets, and apparel outlets.

### Architectural Philosophy: Physical Database-per-Store
Unlike legacy inventory systems that pool multiple businesses into a single monolithic database table separated only by an indexed `store_id` foreign key (leaving tenants vulnerable to cross-tenant data leaks caused by application-layer coding oversights), InventoryPro guarantees absolute data privacy through **Physical Database-per-Store Isolation**:
- **Master Store Registry (`data/master.db`):** Stores global metadata for registered stores (Store Code, Legal Name, Industry, Tax Rate, Status).
- **Isolated Tenant Stores (`data/stores/<STORE_ID>.db`):** Completely independent SQLite databases housing users, products, sales invoices, suppliers, purchase orders, expenses, and audit ledgers.

---

## 2. Multi-Tenant Database Engine

### Dynamic Engine Routing Lifecycle
On every incoming HTTP request:
1. **Session Extraction:** Flask's `@app.before_request` hook extracts `session.get('store_id')`. If unauthenticated, fallback binds to `STORE001`.
2. **Engine Pool Resolution:** The server checks `store_engines.get(store_id)`. If absent, it instantiates an isolated engine:
   ```python
   create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
   ```
3. **Dynamic Scoped Session Binding:**
   ```python
   db.session.bind = store_engines[store_id]
   ```
4. **Context Injection:** `g.current_store` exposes store metadata to Jinja templates.
5. **Atomic Tear-down:** Upon response dispatch, Flask automatically commits or rolls back and returns the connection to the pool.

---

## 3. Relational Schema & Data Dictionary

### Core Tables in each `data/stores/<STORE_ID>.db`

| Table Name | Primary Key | Key Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| **`users`** | `id` (INTEGER) | None | Staff credentials, PBKDF2 hashes, and RBAC roles (`admin`, `manager`, `cashier`). |
| **`categories`** | `id` (INTEGER) | None | Departmental grouping of store products. |
| **`suppliers`** | `id` (INTEGER) | None | Vendor master directory (contact, address, payment terms). |
| **`products`** | `id` (INTEGER) | `category_id`, `supplier_id` | Master catalog of active SKUs, barcodes, cost prices, retail prices, and safety thresholds. |
| **`invoices`** | `id` (INTEGER) | `customer_id`, `user_id` | Immutable ledger of completed sales transactions, subtotals, taxes, and tenders. |
| **`invoice_items`** | `id` (INTEGER) | `invoice_id`, `product_id` | Snapshot of line item quantities, billed unit prices, and historical acquisition cost for COGS auditing. |
| **`purchase_orders`** | `id` (INTEGER) | `supplier_id` | Procurement tracking (`draft` &rarr; `ordered` &rarr; `received`). |
| **`purchase_order_items`**| `id` (INTEGER) | `po_id`, `product_id` | Quantities ordered vs. received with unit procurement cost. |
| **`customers`** | `id` (INTEGER) | None | Client directory, phone, email, and historical purchase balances. |
| **`expenses`** | `id` (INTEGER) | None | Operational overhead ledgers (Rent, Payroll, Utilities, Logistics). |

---

## 4. Role-Based Access Control (RBAC)

Access control is enforced at both the route layer via `@role_required(*roles)` and the UI rendering layer:

| Functional Capability | Cashier (`cashier`) | Store Manager (`manager`) | Store Administrator (`admin`) |
| :--- | :---: | :---: | :---: |
| **Point-of-Sale (POS) Billing & Invoicing** | **✓ YES** | **✓ YES** | **✓ YES** |
| **Print Thermal Slips & A4 PDF Receipts** | **✓ YES** | **✓ YES** | **✓ YES** |
| **Customer Registration at Checkout** | **✓ YES** | **✓ YES** | **✓ YES** |
| **Product Catalog (View Live Stock)** | **✓ YES** | **✓ YES** | **✓ YES** |
| **Add / Edit SKUs & Adjust Stock Levels** | **✕ NO** | **✓ YES** | **✓ YES** |
| **Safety Stock Threshold Management** | **✕ NO** | **✓ YES** | **✓ YES** |
| **Purchase Order Procurement Workflow** | **✕ NO** | **✓ YES** | **✓ YES** |
| **Supplier Master Management (Add/Edit)** | **✕ NO** | **✓ YES** | **✓ YES** |
| **Permanent Supplier Account Deletion** | **✕ NO** | **✕ NO** | **✓ YES** |
| **Executive P&L Statements & COGS Audit** | **✕ NO** | **✓ YES** | **✓ YES** |
| **Staff Provisioning & Credential Reset** | **✕ NO** | **✕ NO** | **✓ YES** |
| **Multi-Tenant Store Context Switching** | **✕ NO** | **✕ NO** | **✓ YES** |

---

## 5. Core Functional Modules & Business Engines

### 5.1 Real-Time Point-of-Sale (POS) & Thermal Invoicing
- **Endpoint:** `/billing/new`
- **Barcode & SKU Instant Search:** Live autocompleting input with automatic price population.
- **Atomic Stock Deductions:** Decrements inventory inside an ACID transaction block, rolling back on insufficient stock.
- **Multi-Payment Acceptance:** Cash, Credit/Debit Card, UPI / QR Code, Bank Transfer.
- **Dual-Print Engine:** Instant thermal 80mm register slip output and full-page A4 PDF tax invoices.

### 5.2 Automated Safety Stock Sentinel & Alerts
- **Endpoint:** `/inventory/alerts`
- Every product maintains a `low_stock_threshold`.
- When stock falls below safety levels, the sentinel triggers dashboard alert badges and surfaces items in the Restock Hub.

### 5.3 Procurement & Closed-Loop Purchase Orders
- **Endpoint:** `/suppliers/po/new`
- **Drafting & Issuance:** Managers select vendors and input purchase quantities.
- **Fulfillment:** Marking a PO as `received` atomically increments warehouse stock counts without manual re-entry.

### 5.4 GAAP Financial Cost Accounting & P&L Engine
- **Endpoint:** `/reports/financial`
- **Gross Revenue:** $\sum \text{Invoice.total\_amount}$
- **Cost of Goods Sold (COGS):** $\sum (\text{Item.quantity} \times \text{Item.unit\_cost})$
- **Gross Profit Margin:** $\text{Gross Revenue} - \text{COGS}$
- **Net Profit:** $\text{Gross Margin} - \text{Expenses} - \text{Tax}$

---

## 6. Complete Route & Endpoint Reference

```
Authentication:
  GET, POST  /auth/login                  Validates credentials and binds tenant DB
  GET, POST  /auth/register               Provisions new store DB or adds staff
  GET        /auth/logout                 Terminates session context

Dashboard:
  GET        /dashboard/                  KPIs, sparklines, velocity chart, restock feed

Products & Catalog:
  GET        /products/                   Paginated product catalog
  GET, POST  /products/add                Add product (Admin, Manager)
  GET, POST  /products/edit/<id>          Edit product (Admin, Manager)
  POST       /products/delete/<id>        Soft-delete product (Admin, Manager)

Inventory & Alerts:
  GET        /inventory/                  Inventory balance ledger
  GET        /inventory/alerts            Restock hub for depleted threshold items

POS Billing & Invoices:
  GET, POST  /billing/new                 POS checkout terminal
  GET        /billing/invoices            Invoice ledger
  GET        /billing/invoice/<id>        Printable invoice details

Suppliers & POs:
  GET, POST  /suppliers/                  Supplier catalog & PO tracking
  GET, POST  /suppliers/po/new            Create purchase order
  POST       /suppliers/po/<id>/status    Update PO status (received auto-stocks)
  POST       /suppliers/<id>/delete       Delete supplier (Admin only)

Financial Reports:
  GET        /reports/financial           P&L Statement, COGS, Net Profit
  POST       /reports/expense/add         Record store overhead
```

---

## 7. Elite SaaS Frontend UX & Keyboard Interaction Engine

### 7.1 Global Command Palette (`Ctrl + K` / `Cmd + K`)
- Press <kbd>Ctrl</kbd> + <kbd>K</kbd> anywhere across the app.
- Search actions, jump to routes, or switch tenant databases instantly without logging out.

### 7.2 Two-Key Chord Navigation Engine (`G` Chords)
Outside of form input fields:
- <kbd>G</kbd> then <kbd>B</kbd> &rarr; **Go to Billing** (POS Terminal)
- <kbd>G</kbd> then <kbd>D</kbd> &rarr; **Go to Dashboard**
- <kbd>G</kbd> then <kbd>P</kbd> &rarr; **Go to Products**
- <kbd>G</kbd> then <kbd>I</kbd> &rarr; **Go to Inventory**
- <kbd>G</kbd> then <kbd>A</kbd> &rarr; **Go to Alerts**
- <kbd>T</kbd> &rarr; **Toggle Dark / Light Theme**

### 7.3 Mouse-Tracking Spotlights & SVG Sparklines
- Cards marked with `[data-spotlight="true"]` track cursor position dynamically via CSS variables `--mouse-x` and `--mouse-y`.
- Stat cards feature animated SVG micro-sparklines with `stroke-dashoffset` keyframe physics.

---

## 8. Security Governance & Threat Defense Model
- **Cryptographic Key Derivation:** Passwords protected via PBKDF2/SHA-256 with random salts.
- **CSRF Defense:** Every POST form validates a cryptographically signed anti-CSRF token via Flask-WTF.
- **SQL Injection Immunity:** All queries use parameterized SQLAlchemy ORM mappings.
- **Session Protection:** Encrypted HTTP-only cookies signed with server `SECRET_KEY`.

---

## 9. Installation, Seeding & Production Deployment Guide

### Quick Start
```bash
# 1. Clone repository & create virtual environment
git clone <repo-url>
cd semester_project
python -m venv venv
venv\Scripts\activate   # Windows (or source venv/bin/activate on Unix)

# 2. Install dependencies
pip install flask flask-sqlalchemy flask-login flask-wtf reportlab pymupdf

# 3. Seed demo multi-tenant stores (TechMart, GreenLeaf, CarePlus)
python seed_data.py

# 4. Start development server
python app.py
```
Visit `http://127.0.0.1:5000/` in your browser.

### Production WSGI
- **Linux:** `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
- **Windows:** `waitress-serve --port=5000 app:app`

---

## 10. Automated Verification Test Suites

```bash
# Verify multi-tenant database isolation & tenant creation
python scratch/test_multitenant_flow.py

# Verify live dynamic sales velocity charting & zero-state overlays
python scratch/test_chart_dynamic.py

# Verify Command Palette, Sparklines, and UI micro-physics
python scratch/test_advance_ui.py
```
*All test suites pass with 100% success.*
