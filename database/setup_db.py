import sqlite3
import random
from datetime import datetime, timedelta

def create_schema(cursor):
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
        city TEXT,
        state TEXT,
        country TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        description TEXT
    );
    """)

    # 3. Suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        country TEXT,
        city TEXT,
        rating REAL CHECK(rating BETWEEN 1 AND 5)
    );
    """)

    # 4. Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        supplier_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE,
        price REAL CHECK(price >= 0),
        stock_quantity INTEGER CHECK(stock_quantity >= 0),
        weight REAL,
        rating REAL CHECK(rating BETWEEN 1 AND 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id),
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
    );
    """)

    # 5. Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT CHECK(status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
        total_amount REAL CHECK(total_amount >= 0),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );
    """)

    # 6. Order_Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Order_Items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER CHECK(quantity > 0),
        unit_price REAL CHECK(unit_price >= 0),
        discount REAL CHECK(discount >= 0 AND discount <= 100),
        subtotal REAL CHECK(subtotal >= 0),
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id)
    );
    """)

    # 7. Payments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_method TEXT CHECK(payment_method IN ('Credit Card', 'Debit Card', 'PayPal', 'UPI', 'Cash on Delivery')),
        transaction_id TEXT,
        payment_status TEXT CHECK(payment_status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
        amount REAL CHECK(amount >= 0),
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id)
    );
    """)

    # 8. Shipping
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Shipping (
        shipping_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        courier_name TEXT,
        tracking_number TEXT,
        shipping_status TEXT CHECK(shipping_status IN ('Processing', 'In Transit', 'Out for Delivery', 'Delivered', 'Returned')),
        estimated_delivery DATE,
        actual_delivery DATE,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id)
    );
    """)

    # 9. Reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        product_id INTEGER,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        review_text TEXT,
        review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id)
    );
    """)

    # Indexes
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_customers_city ON Customers(city);",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON Products(category_id);",
        "CREATE INDEX IF NOT EXISTS idx_products_supplier ON Products(supplier_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON Orders(customer_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_date ON Orders(order_date);",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order ON Order_Items(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_order_items_product ON Order_Items(product_id);",
        "CREATE INDEX IF NOT EXISTS idx_payments_order ON Payments(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_shipping_order ON Shipping(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_reviews_product ON Reviews(product_id);"
    ]
    for idx_q in index_queries:
        cursor.execute(idx_q)

    # View
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS CustomerOrderSummary AS
    SELECT 
        c.customer_id, c.first_name, c.last_name, c.email,
        o.order_id, o.order_date, o.status as order_status, o.total_amount,
        p.payment_method, p.payment_status,
        s.courier_name, s.shipping_status
    FROM Customers c
    JOIN Orders o ON c.customer_id = o.customer_id
    LEFT JOIN Payments p ON o.order_id = p.order_id
    LEFT JOIN Shipping s ON o.order_id = s.order_id;
    """)
    print("Schema created successfully.")

def seed_data(cursor):
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM Customers")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded. Skipping.")
        return

    print("Seeding database...")
    
    # Insert Categories
    categories = [
        ("Electronics", "Gadgets and electronic devices"),
        ("Fashion", "Clothing and accessories"),
        ("Books", "Printed and electronic books"),
        ("Home", "Home decor and appliances"),
        ("Sports", "Sports equipment and apparel")
    ]
    cursor.executemany("INSERT INTO Categories (category_name, description) VALUES (?, ?)", categories)

    # Insert Suppliers
    suppliers = [
        ("TechHub Inc", "contact@techhub.com", "1234567890", "USA", "New York", 4.8),
        ("Global Fashion", "sales@globalfashion.com", "0987654321", "UK", "London", 4.2),
        ("Readers Choice", "info@readerschoice.com", "1122334455", "India", "Delhi", 4.5),
        ("Home Goods Co", "support@homegoods.com", "5566778899", "China", "Shenzhen", 4.0)
    ]
    cursor.executemany("INSERT INTO Suppliers (supplier_name, email, phone, country, city, rating) VALUES (?, ?, ?, ?, ?, ?)", suppliers)

    # Insert Products
    products = [
        (1, 1, "Smartphone X", "Latest 5G smartphone", "SKU-ELEC-001", 699.99, 100, 0.2, 4.5),
        (1, 1, "Wireless Headphones", "Noise cancelling headphones", "SKU-ELEC-002", 149.99, 200, 0.3, 4.7),
        (1, 1, "4K Monitor", "27-inch 4K UHD Monitor", "SKU-ELEC-003", 349.99, 50, 5.0, 4.2),
        (2, 2, "Men's T-Shirt", "100% Cotton T-Shirt", "SKU-FASH-001", 19.99, 500, 0.1, 4.0),
        (2, 2, "Running Shoes", "Lightweight sports shoes", "SKU-FASH-002", 79.99, 150, 0.8, 4.3),
        (3, 3, "Python Programming", "Learn Python in 30 days", "SKU-BOOK-001", 39.99, 300, 1.2, 4.8),
        (4, 4, "Coffee Maker", "Automatic drip coffee maker", "SKU-HOME-001", 49.99, 80, 2.5, 4.1),
        (5, 2, "Yoga Mat", "Non-slip exercise mat", "SKU-SPRT-001", 24.99, 200, 1.5, 4.6)
    ]
    cursor.executemany("INSERT INTO Products (category_id, supplier_id, name, description, sku, price, stock_quantity, weight, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", products)

    # Insert Customers
    customers = [
        ("Amit", "Sharma", "amit@example.com", "9876543210", "1990-05-15", "Male", "Delhi", "Delhi", "India"),
        ("Priya", "Singh", "priya@example.com", "9876543211", "1992-08-20", "Female", "Mumbai", "Maharashtra", "India"),
        ("John", "Doe", "john@example.com", "1231231234", "1985-11-10", "Male", "New York", "NY", "USA"),
        ("Emily", "Clark", "emily@example.com", "4564564567", "1995-02-25", "Female", "London", "England", "UK")
    ]
    cursor.executemany("INSERT INTO Customers (first_name, last_name, email, phone, date_of_birth, gender, city, state, country) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers)

    # Insert Orders & Related items
    # We will generate a few orders manually
    orders_data = [
        (1, "Delivered", 849.98), # Amit ordered Smartphone + Headphones
        (2, "Shipped", 79.99),    # Priya ordered Shoes
        (3, "Pending", 89.98),    # John ordered Book + Coffee Maker
        (1, "Cancelled", 349.99)  # Amit cancelled Monitor
    ]
    
    # Dates for orders
    base_date = datetime.now() - timedelta(days=30)
    
    for i, (cust_id, status, total) in enumerate(orders_data):
        order_date = base_date + timedelta(days=i*5)
        cursor.execute("INSERT INTO Orders (customer_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)", 
                       (cust_id, order_date.strftime("%Y-%m-%d %H:%M:%S"), status, total))
        order_id = cursor.lastrowid
        
        # Insert Order Items based on the order
        if i == 0:
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 1, 1, 699.99, 0, 699.99))
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 2, 1, 149.99, 0, 149.99))
            # Payment
            cursor.execute("INSERT INTO Payments (order_id, payment_method, transaction_id, payment_status, amount) VALUES (?, ?, ?, ?, ?)", (order_id, "Credit Card", "TXN001", "Completed", 849.98))
            # Shipping
            cursor.execute("INSERT INTO Shipping (order_id, courier_name, tracking_number, shipping_status) VALUES (?, ?, ?, ?)", (order_id, "FedEx", "TRK001", "Delivered"))
            
        elif i == 1:
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 5, 1, 79.99, 0, 79.99))
            cursor.execute("INSERT INTO Payments (order_id, payment_method, transaction_id, payment_status, amount) VALUES (?, ?, ?, ?, ?)", (order_id, "UPI", "TXN002", "Completed", 79.99))
            cursor.execute("INSERT INTO Shipping (order_id, courier_name, tracking_number, shipping_status) VALUES (?, ?, ?, ?)", (order_id, "BlueDart", "TRK002", "In Transit"))
            
        elif i == 2:
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 6, 1, 39.99, 0, 39.99))
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 7, 1, 49.99, 0, 49.99))
            cursor.execute("INSERT INTO Payments (order_id, payment_method, transaction_id, payment_status, amount) VALUES (?, ?, ?, ?, ?)", (order_id, "PayPal", "TXN003", "Pending", 89.98))
            cursor.execute("INSERT INTO Shipping (order_id, courier_name, tracking_number, shipping_status) VALUES (?, ?, ?, ?)", (order_id, "DHL", "TRK003", "Processing"))
            
        elif i == 3:
            cursor.execute("INSERT INTO Order_Items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?)", (order_id, 3, 1, 349.99, 0, 349.99))
            cursor.execute("INSERT INTO Payments (order_id, payment_method, transaction_id, payment_status, amount) VALUES (?, ?, ?, ?, ?)", (order_id, "Credit Card", "TXN004", "Refunded", 349.99))

    # Insert a few reviews
    reviews = [
        (1, 1, 5, "Amazing phone, very fast!"),
        (1, 2, 4, "Good sound quality but a bit heavy."),
        (2, 5, 5, "Very comfortable for running.")
    ]
    cursor.executemany("INSERT INTO Reviews (customer_id, product_id, rating, review_text) VALUES (?, ?, ?, ?)", reviews)

    print("Seed data inserted successfully.")

if __name__ == "__main__":
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    
    create_schema(cursor)
    seed_data(cursor)
    
    conn.commit()
    conn.close()
    print("Database setup complete.")
