from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     FloatField, IntegerField, DateField, SubmitField, HiddenField, RadioField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class LoginForm(FlaskForm):
    store_id = StringField('Store ID / Code', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    reg_type = SelectField('Registration Type', choices=[
        ('new_store', 'Register New Store / Industry (Become Store Owner)'),
        ('join_store', 'Join Existing Store as Staff (Manager / Cashier)')
    ], default='new_store')
    store_id = StringField('Store ID / Code', validators=[DataRequired(), Length(min=2, max=50)])
    store_name = StringField('Store Name', validators=[Optional(), Length(max=150)])
    industry = SelectField('Industry Sector', choices=[
        ('Consumer Electronics & IT', 'Consumer Electronics & IT Gadgets'),
        ('Supermarket & Grocery', 'Supermarket, Grocery & Organics'),
        ('Fashion & Apparel', 'Clothing, Apparel & Footwear'),
        ('Pharmacy & Healthcare', 'Pharmacy, Medical & Healthcare'),
        ('Hardware & Industrial', 'Hardware, Tools & Industrial Supplies'),
        ('Stationery & Books', 'Stationery, Books & Office Supplies'),
        ('General Retail', 'Departmental & General Retail Store')
    ], default='General Retail')
    role = SelectField('Role', choices=[
        ('admin', 'Store Admin / Owner'),
        ('manager', 'Store Manager'),
        ('cashier', 'POS Cashier')
    ], default='admin')
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    cost_price = FloatField('Cost Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField('Low Stock Threshold', validators=[Optional(), NumberRange(min=0)], default=10)
    unit = StringField('Unit', validators=[Optional()], default='pcs')
    submit = SubmitField('Save Product')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')


class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(max=200)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Supplier')


class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Customer')


class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    expected_delivery = DateField('Expected Delivery', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Purchase Order')


class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired(), Length(max=300)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('rent', 'Rent'), ('utilities', 'Utilities'), ('salary', 'Salary'),
        ('maintenance', 'Maintenance'), ('marketing', 'Marketing'),
        ('supplies', 'Office Supplies'), ('other', 'Other')
    ])
    date = DateField('Date', validators=[Optional()])
    submit = SubmitField('Save Expense')
