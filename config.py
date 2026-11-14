import os

basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
stores_dir = os.path.join(data_dir, 'stores')

os.makedirs(stores_dir, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'inventory-mgmt-secret-key-2024')
    DATA_DIR = data_dir
    STORES_DIR = stores_dir
    MASTER_DB_PATH = os.path.join(data_dir, 'master.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(data_dir, 'master.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_STOCK_THRESHOLD = 10
