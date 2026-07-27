import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, 
    CheckConstraint, Index, Text, Enum
)
from sqlalchemy.orm import relationship
from database.connection import Base
from sqlalchemy.sql import func
import enum

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class TimestampMixin:
    """Mixin to add created_at and updated_at columns."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")
    reviews = relationship("Review", back_populates="customer")
    addresses = relationship("Address", back_populates="customer")
    wishlists = relationship("Wishlist", back_populates="customer")
    notifications = relationship("Notification", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")

class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    products = relationship("Product", back_populates="category")

class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    rating = Column(Float, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=True)
    
    products = relationship("Product", back_populates="supplier")

class Product(Base, TimestampMixin):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    price = Column(Float, CheckConstraint('price >= 0'), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False)

class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    status = Column(String(50), nullable=False, default=OrderStatus.PENDING.value, index=True)
    total_amount = Column(Float, CheckConstraint('total_amount >= 0'), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)
    shipping = relationship("Shipping", back_populates="order", uselist=False)
    returns = relationship("Return", back_populates="order")
    coupon = relationship("Coupon", back_populates="orders")

class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    quantity = Column(Integer, CheckConstraint('quantity > 0'), nullable=False)
    unit_price = Column(Float, CheckConstraint('unit_price >= 0'), nullable=False)
    subtotal = Column(Float, CheckConstraint('subtotal >= 0'), nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    
    amount = Column(Float, CheckConstraint('amount >= 0'), nullable=False)
    payment_method = Column(String(50), nullable=False) # e.g. Credit Card, PayPal
    status = Column(String(50), nullable=False, default="PENDING")
    transaction_id = Column(String(100), unique=True, nullable=True)
    
    order = relationship("Order", back_populates="payment")

class Shipping(Base, TimestampMixin):
    __tablename__ = "shipping"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    
    carrier = Column(String(50), nullable=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="PROCESSING")
    estimated_delivery = Column(DateTime, nullable=True)
    
    order = relationship("Order", back_populates="shipping")
    address = relationship("Address")

class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)
    comment = Column(Text, nullable=True)
    
    customer = relationship("Customer", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

class Wishlist(Base, TimestampMixin):
    __tablename__ = "wishlists"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    customer = relationship("Customer", back_populates="wishlists")
    product = relationship("Product")
    
    __table_args__ = (
        Index('idx_customer_product_wishlist', 'customer_id', 'product_id', unique=True),
    )

class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True)
    
    warehouse_location = Column(String(100), nullable=False)
    stock_level = Column(Integer, CheckConstraint('stock_level >= 0'), nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    
    product = relationship("Product", back_populates="inventory")

class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    discount_percentage = Column(Float, CheckConstraint('discount_percentage > 0 AND discount_percentage <= 100'), nullable=False)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    orders = relationship("Order", back_populates="coupon")

class Return(Base, TimestampMixin):
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    reason = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    
    order = relationship("Order", back_populates="returns")
    product = relationship("Product")

class Admin(Base, TimestampMixin):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="MANAGER") # SUPERADMIN, MANAGER, SUPPORT
    
    audit_logs = relationship("AuditLog", back_populates="admin")

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True) # Could be admin_id or customer_id
    user_type = Column(String(20), nullable=False) # 'CUSTOMER' or 'ADMIN'
    
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False, index=True)
    
    action = Column(String(100), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    
    admin = relationship("Admin", back_populates="audit_logs")

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    
    customer = relationship("Customer", back_populates="notifications")

class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, IN_PROGRESS, RESOLVED
    priority = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH
    
    customer = relationship("Customer", back_populates="support_tickets")

class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    address_type = Column(String(20), nullable=False) # BILLING, SHIPPING
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    
    customer = relationship("Customer", back_populates="addresses")

class QueryHistory(Base, TimestampMixin):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=True, index=True)
    user_question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    is_successful = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
