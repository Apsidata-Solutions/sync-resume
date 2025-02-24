from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    DECIMAL, Text, ForeignKey, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Define the base class for declarative models
Base = declarative_base()

# 1. Customers Table
class Customer(Base):
    __tablename__ = 'customers'
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False)
    email = Column(String(100))
    address = Column(String(255))
    
    # Relationship to Orders
    orders = relationship("Order", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.customer_id}, name='{self.name}', phone='{self.phone_number}')>"

# 2. Orders Table
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False)
    order_date = Column(DateTime, default=func.now())
    pickup_date = Column(DateTime)
    total_amount = Column(DECIMAL(10, 2))
    status = Column(String(50), default="New")
    notes = Column(Text)
    invoice_sent = Column(Boolean, default=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.order_id}, customer_id={self.customer_id}, status='{self.status}')>"

# 3. Order_Items Table
class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(DECIMAL(10, 2))
    special_instructions = Column(Text)
    
    # Relationship
    order = relationship("Order", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.item_id}, order_id={self.order_id}, description='{self.item_description}')>"
    
    # # Create a session
    # Session = sessionmaker(bind=engine)
    # session = Session()
    
    # # Example: Add a customer
    # new_customer = Customer(
    #     name="John Doe", 
    #     phone_number="1234567890", 
    #     email="johndoe@example.com", 
    #     address="123 Example St"
    # )
    # session.add(new_customer)
    # session.commit()
    
    # # Example: Create an order for the customer
    # new_order = Order(
    #     customer_id=new_customer.customer_id,
    #     pickup_date=None,  # Can set a datetime object if needed
    #     status="New",
    #     total_amount=0.0,
    #     notes="No special instructions",
    #     invoice_sent=False
    # )
    # session.add(new_order)
    # session.commit()
    
    # # Example: Add an order item for the order
    # new_order_item = OrderItem(
    #     order_id=new_order.order_id,
    #     item_description="Shirt dry cleaning",
    #     quantity=3,
    #     special_instructions="Handle gently",
    #     price=150.00
    # )
    # session.add(new_order_item)
    # session.commit()
    
    # print("Database created and sample data inserted!")