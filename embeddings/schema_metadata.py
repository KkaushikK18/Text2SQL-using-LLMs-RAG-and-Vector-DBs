TABLE_METADATA = {
    "Customers": {
        "description": "Stores information about customers including their names, email, phone, location (city, state, country), date of birth, and gender.",
        "schema": "customer_id (INTEGER PRIMARY KEY), first_name (TEXT), last_name (TEXT), email (TEXT), phone (TEXT), date_of_birth (DATE), gender (TEXT), city (TEXT), state (TEXT), country (TEXT), created_at (TIMESTAMP)"
    },
    "Categories": {
        "description": "Stores product categories like Electronics, Fashion, Books, Home, etc.",
        "schema": "category_id (INTEGER PRIMARY KEY), category_name (TEXT), description (TEXT)"
    },
    "Suppliers": {
        "description": "Stores information about suppliers or vendors who provide the products. Includes contact details and ratings.",
        "schema": "supplier_id (INTEGER PRIMARY KEY), supplier_name (TEXT), email (TEXT), phone (TEXT), country (TEXT), city (TEXT), rating (REAL)"
    },
    "Products": {
        "description": "Stores details about the products being sold. Includes price, stock_quantity, SKU, weight, rating, and links to categories and suppliers.",
        "schema": "product_id (INTEGER PRIMARY KEY), category_id (INTEGER), supplier_id (INTEGER), name (TEXT), description (TEXT), sku (TEXT), price (REAL), stock_quantity (INTEGER), weight (REAL), rating (REAL), created_at (TIMESTAMP)\nForeign Keys: category_id -> Categories(category_id), supplier_id -> Suppliers(supplier_id)"
    },
    "Orders": {
        "description": "Stores high-level order information for customers. Includes the total_amount, order_date, and status (Pending, Shipped, Delivered, Cancelled). Does NOT contain specific products.",
        "schema": "order_id (INTEGER PRIMARY KEY), customer_id (INTEGER), order_date (TIMESTAMP), status (TEXT), total_amount (REAL)\nForeign Keys: customer_id -> Customers(customer_id)"
    },
    "Order_Items": {
        "description": "Stores the specific products purchased inside an order. Contains the quantity, unit_price, discount, and subtotal for each product in an order. Essential for revenue or product popularity questions.",
        "schema": "order_item_id (INTEGER PRIMARY KEY), order_id (INTEGER), product_id (INTEGER), quantity (INTEGER), unit_price (REAL), discount (REAL), subtotal (REAL)\nForeign Keys: order_id -> Orders(order_id), product_id -> Products(product_id)"
    },
    "Payments": {
        "description": "Stores payment transactions for orders. Includes payment_method (Credit Card, UPI, etc.), payment_status, transaction_id, and amount.",
        "schema": "payment_id (INTEGER PRIMARY KEY), order_id (INTEGER), payment_method (TEXT), transaction_id (TEXT), payment_status (TEXT), amount (REAL), payment_date (TIMESTAMP)\nForeign Keys: order_id -> Orders(order_id)"
    },
    "Shipping": {
        "description": "Stores shipping and delivery information for orders. Includes courier_name, tracking_number, shipping_status, and delivery dates.",
        "schema": "shipping_id (INTEGER PRIMARY KEY), order_id (INTEGER), courier_name (TEXT), tracking_number (TEXT), shipping_status (TEXT), estimated_delivery (DATE), actual_delivery (DATE)\nForeign Keys: order_id -> Orders(order_id)"
    },
    "Reviews": {
        "description": "Stores customer reviews and ratings for products. Contains the review_text and rating (1-5).",
        "schema": "review_id (INTEGER PRIMARY KEY), customer_id (INTEGER), product_id (INTEGER), rating (INTEGER), review_text (TEXT), review_date (TIMESTAMP)\nForeign Keys: customer_id -> Customers(customer_id), product_id -> Products(product_id)"
    },
    "CustomerOrderSummary": {
        "description": "A view that combines Customers, Orders, Payments, and Shipping for easy access to high-level order tracking details.",
        "schema": "customer_id, first_name, last_name, email, order_id, order_date, order_status, total_amount, payment_method, payment_status, courier_name, shipping_status"
    }
}
