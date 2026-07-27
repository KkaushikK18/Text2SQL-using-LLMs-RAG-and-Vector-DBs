import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from database.connection import engine, Base, SessionLocal
from database.models import (
    Customer, Category, Supplier, Product, Order, OrderItem, 
    Payment, Shipping, Review, Wishlist, Inventory, Coupon, 
    Return, Admin, Session as UserSession, AuditLog, 
    Notification, SupportTicket, Address, OrderStatus
)
from utils.logger import get_logger

logger = get_logger("SeedData")

# Deterministic generation
Faker.seed(42)
random.seed(42)
fake = Faker()

def recreate_database():
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)

def generate_data(session: Session):
    logger.info("Starting synthetic data generation...")
    
    # 1. Categories (25)
    categories = []
    category_names = set()
    while len(category_names) < 25:
        category_names.add(fake.word().capitalize() + " " + fake.word().capitalize())
    
    for name in category_names:
        categories.append(Category(name=name, description=fake.sentence()))
    session.add_all(categories)
    session.commit()
    logger.info(f"Inserted {len(categories)} categories.")
    
    # 2. Suppliers (100)
    suppliers = []
    supplier_names = set()
    while len(supplier_names) < 100:
        supplier_names.add(fake.company())
        
    for name in supplier_names:
        suppliers.append(Supplier(
            name=name,
            email=fake.company_email(),
            phone=fake.phone_number()[:20],
            rating=round(random.uniform(2.0, 5.0), 1)
        ))
    session.add_all(suppliers)
    session.commit()
    logger.info("Inserted 100 suppliers.")
    
    # 3. Products (500) and Inventory (500)
    products = []
    category_ids = [c.id for c in session.query(Category.id).all()]
    supplier_ids = [s.id for s in session.query(Supplier.id).all()]
    
    for i in range(500):
        p = Product(
            category_id=random.choice(category_ids),
            supplier_id=random.choice(supplier_ids),
            name=fake.catch_phrase(),
            description=fake.text(),
            sku=fake.unique.bothify(text='SKU-????-####'),
            price=round(random.uniform(5.0, 1000.0), 2),
            is_active=random.choice([True, True, True, False])
        )
        products.append(p)
    session.add_all(products)
    session.commit()
    
    product_ids = [p.id for p in session.query(Product.id).all()]
    inventories = []
    for pid in product_ids:
        inventories.append(Inventory(
            product_id=pid,
            warehouse_location=fake.city(),
            stock_level=random.randint(0, 500),
            reorder_threshold=random.randint(5, 20)
        ))
    session.add_all(inventories)
    session.commit()
    logger.info("Inserted 500 products and inventory records.")
    
    # 4. Customers (1000) and Addresses (2000)
    customers = []
    for _ in range(1000):
        customers.append(Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.unique.phone_number()[:20],
            is_active=True
        ))
    session.add_all(customers)
    session.commit()
    
    customer_ids = [c.id for c in session.query(Customer.id).all()]
    addresses = []
    for cid in customer_ids:
        addresses.append(Address(
            customer_id=cid,
            address_type="BILLING",
            street=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            postal_code=fake.postcode(),
            country=fake.country()
        ))
        addresses.append(Address(
            customer_id=cid,
            address_type="SHIPPING",
            street=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            postal_code=fake.postcode(),
            country=fake.country()
        ))
    session.bulk_save_objects(addresses)
    session.commit()
    logger.info("Inserted 1000 customers and 2000 addresses.")
    
    # 5. Coupons (50)
    coupons = []
    for _ in range(50):
        coupons.append(Coupon(
            code=fake.unique.bothify(text='PROMO-####-????'),
            discount_percentage=round(random.uniform(5.0, 50.0), 2),
            valid_until=datetime.now() + timedelta(days=random.randint(10, 365)),
            is_active=random.choice([True, False])
        ))
    session.add_all(coupons)
    session.commit()
    coupon_ids = [c.id for c in session.query(Coupon.id).all()]
    
    # 6. Orders (10000), Order Items (30000), Payments (10000), Shipping (10000)
    logger.info("Generating 10,000 Orders. This might take a moment...")
    
    # Fetch all prices to calculate subtotals quickly without DB hits inside the loop
    product_prices = dict(session.query(Product.id, Product.price).all())
    
    orders = []
    order_items = []
    payments = []
    shippings = []
    
    # Let's generate orders in memory first to use bulk_insert
    # Need to keep track of order IDs manually for relationships in bulk insert, 
    # but SQLAlchemy doesn't return IDs on bulk_insert_mappings for SQLite easily.
    # We will do batch inserts of 1000 instead of 1 by 1.
    
    batch_size = 1000
    for batch in range(10):
        orders_batch = []
        for i in range(batch_size):
            o = Order(
                customer_id=random.choice(customer_ids),
                status=random.choice([s.value for s in OrderStatus]),
                total_amount=0.0, # Will update later
                coupon_id=random.choice(coupon_ids + [None, None, None])
            )
            orders_batch.append(o)
        
        session.add_all(orders_batch)
        session.flush() # Gets IDs for orders without full commit
        
        items_batch = []
        payments_batch = []
        shipping_batch = []
        
        for o in orders_batch:
            # 1 to 5 items per order
            num_items = random.randint(1, 5)
            order_total = 0.0
            
            for _ in range(num_items):
                pid = random.choice(product_ids)
                qty = random.randint(1, 3)
                price = product_prices[pid]
                sub = qty * price
                order_total += sub
                
                items_batch.append(OrderItem(
                    order_id=o.id,
                    product_id=pid,
                    quantity=qty,
                    unit_price=price,
                    subtotal=sub
                ))
            
            # Apply fake coupon discount roughly
            if o.coupon_id:
                order_total *= 0.9 # Just approx for speed
            o.total_amount = round(order_total, 2)
            
            # Payment
            payments_batch.append(Payment(
                order_id=o.id,
                amount=o.total_amount,
                payment_method=random.choice(["Credit Card", "PayPal", "Debit Card", "UPI", "Stripe"]),
                status=random.choice(["COMPLETED", "COMPLETED", "PENDING", "FAILED"]),
                transaction_id=fake.unique.uuid4()
            ))
            
            # Shipping
            shipping_batch.append(Shipping(
                order_id=o.id,
                address_id=random.choice(range(1, 2001)), # Rough address range
                carrier=random.choice(["FedEx", "UPS", "USPS", "DHL"]),
                tracking_number=fake.bothify(text='TRK##########'),
                status=random.choice(["PROCESSING", "SHIPPED", "DELIVERED", "RETURNED"]),
                estimated_delivery=datetime.now() + timedelta(days=random.randint(1, 10))
            ))
            
        session.bulk_save_objects(items_batch)
        session.bulk_save_objects(payments_batch)
        session.bulk_save_objects(shipping_batch)
        session.commit()
        logger.info(f" -> Committed batch {batch+1}/10 of Orders.")
        
    logger.info("Inserted 10,000 Orders, Payments, Shippings, and ~30,000 Order_Items.")
    
    # 7. Reviews (5000)
    reviews = []
    for _ in range(5000):
        reviews.append(Review(
            customer_id=random.choice(customer_ids),
            product_id=random.choice(product_ids),
            rating=random.randint(1, 5),
            comment=fake.text() if random.choice([True, False]) else None
        ))
    session.bulk_save_objects(reviews)
    session.commit()
    logger.info("Inserted 5000 Reviews.")
    
    logger.info("Synthetic data generation completed successfully!")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        recreate_database()
        generate_data(db)
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
    finally:
        db.close()
