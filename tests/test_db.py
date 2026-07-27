import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.connection import SessionLocal
from database.models import Customer, Product, Order

def test_database_connection():
    db = SessionLocal()
    assert db is not None
    db.close()

def test_customers_exist():
    db = SessionLocal()
    count = db.query(Customer).count()
    assert count > 0, "No customers found in database."
    db.close()

def test_products_exist():
    db = SessionLocal()
    count = db.query(Product).count()
    assert count > 0, "No products found in database."
    db.close()

def test_orders_exist():
    db = SessionLocal()
    count = db.query(Order).count()
    assert count > 0, "No orders found in database."
    db.close()
