from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import bcrypt

# Create FastAPI app
app = FastAPI(
    title="E-commerce API belongs to freddy",
    description="Complete e-commerce API with products, users, cart, and checkout",
    version="1.0.0"
)

# ========================
# 1. SETUP & MODELS
# ========================

# Pydantic models
class Product(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

class CartItem(BaseModel):
    product_id: int
    quantity: int

class CartResponse(BaseModel):
    user_id: int
    items: List[dict]
    total_items: int

class CheckoutResponse(BaseModel):
    user_id: int
    items: List[dict]
    subtotal: float
    total: float
    message: str

# ========================
# 2. SAMPLE DATA
# ========================

# Sample products
sample_products = [
    {
        "id": 1,
        "name": "iPhone 15 Pro",
        "description": "Latest iPhone with advanced camera",
        "price": 999.99,
        "image": "https://example.com/iphone15.jpg"
    },
    {
        "id": 2,
        "name": "Samsung Galaxy S23",
        "description": "Powerful Android smartphone",
        "price": 899.99,
        "image": "https://example.com/galaxy_s23.jpg"
    },
    {
        "id": 3,
        "name": "MacBook Air M2",
        "description": "Ultra-thin laptop with M2 chip",
        "price": 1299.99,
        "image": "https://example.com/macbook_air.jpg"
    },
    {
        "id": 4,
        "name": "Sony Headphones",
        "description": "Wireless noise-canceling headphones",
        "price": 349.99,
        "image": "https://example.com/sony_headphones.jpg"
    },
    {
        "id": 5,
        "name": "Nike Shoes",
        "description": "Classic basketball shoes",
        "price": 175.99,
        "image": "https://example.com/nike_shoes.jpg"
    }
]

# In-memory storage
users_db = []
next_user_id = 1

# Cart storage: {user_id: [{"product_id": int, "quantity": int}, ...]}
carts_db = {}

# ========================
# 3. HELPER FUNCTIONS
# ========================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def find_user_by_username(username: str):
    """Find user by username"""
    for user in users_db:
        if user["username"] == username:
            return user
    return None

def find_user_by_email(email: str):
    """Find user by email"""
    for user in users_db:
        if user["email"] == email:
            return user
    return None

def find_user_by_username_or_email(identifier: str):
    """Find user by username or email"""
    if "@" in identifier:
        return find_user_by_email(identifier)
    else:
        return find_user_by_username(identifier)

def find_product_by_id(product_id: int):
    """Find product by ID"""
    for product in sample_products:
        if product["id"] == product_id:
            return product
    return None

# ========================
# 4. ROUTES
# ========================

# ------------------------
# 1. SETUP - Root endpoint
# ------------------------
@app.get("/")
def root():
    """Root endpoint - Welcome message"""
    return {"message": "Welcome to our E-commerce API"}

# ------------------------
# 2. PRODUCTS - Get products
# ------------------------
@app.get("/products", response_model=List[Product])
def get_all_products():
    """Get all products"""
    return sample_products

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """Get product by ID"""
    product = find_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

# ------------------------
# 3. USERS - Register & Login
# ------------------------
@app.post("/register", response_model=UserResponse)
def register_user(user_data: UserRegister):
    """Register a new user"""
    global next_user_id
    
    # Check if username exists
    if find_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email exists
    if find_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = {
        "id": next_user_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hash_password(user_data.password)
    }
    
    users_db.append(new_user)
    next_user_id += 1
    
    # Initialize empty cart for user
    carts_db[new_user["id"]] = []
    
    return {
        "id": new_user["id"],
        "username": new_user["username"],
        "email": new_user["email"]
    }

@app.post("/login")
def login_user(login_data: UserLogin):
    """Login user"""
    user = find_user_by_username_or_email(login_data.username_or_email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

# ------------------------
# 4. CART - Add to cart & View cart
# ------------------------
@app.post("/cart")
def add_to_cart(cart_item: CartItem, user_id: int):
    """Add product to user's cart"""
    # Check if user exists
    user_exists = any(user["id"] == user_id for user in users_db)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if product exists
    product = find_product_by_id(cart_item.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Initialize cart if not exists
    if user_id not in carts_db:
        carts_db[user_id] = []
    
    # Check if product already in cart
    cart = carts_db[user_id]
    for item in cart:
        if item["product_id"] == cart_item.product_id:
            item["quantity"] += cart_item.quantity
            break
    else:
        # Product not in cart, add new item
        cart.append({
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity
        })
    
    return {
        "message": "Product added to cart",
        "cart_item": cart_item,
        "user_id": user_id
    }

@app.get("/cart/{user_id}", response_model=CartResponse)
def get_cart(user_id: int):
    """Get user's cart with product details"""
    if user_id not in carts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found for this user"
        )
    
    cart_items = []
    total_items = 0
    
    for cart_item in carts_db[user_id]:
        product = find_product_by_id(cart_item["product_id"])
        if product:
            item_total = product["price"] * cart_item["quantity"]
            cart_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": cart_item["quantity"],
                "item_total": item_total,
                "image": product["image"]
            })
            total_items += cart_item["quantity"]
    
    return {
        "user_id": user_id,
        "items": cart_items,
        "total_items": total_items
    }

# ------------------------
# 5. CHECKOUT - Process order
# ------------------------
@app.post("/checkout/{user_id}", response_model=CheckoutResponse)
def checkout(user_id: int):
    """Process checkout for user's cart"""
    if user_id not in carts_db or not carts_db[user_id]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    cart_items = []
    subtotal = 0.0
    
    # Calculate totals
    for cart_item in carts_db[user_id]:
        product = find_product_by_id(cart_item["product_id"])
        if product:
            item_total = product["price"] * cart_item["quantity"]
            cart_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": cart_item["quantity"],
                "item_total": item_total
            })
            subtotal += item_total
    
    # Clear cart after checkout
    carts_db[user_id] = []
    
    return {
        "user_id": user_id,
        "items": cart_items,
        "subtotal": subtotal,
        "total": subtotal,  # No taxes/shipping in this example
        "message": "Order placed successfully!"
    }

# ------------------------
# EXTRA: Get all users (for testing)
# ------------------------
@app.get("/users", response_model=List[UserResponse])
def get_all_users():
    """Get all registered users (for testing)"""
    return [
        {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
        for user in users_db
    ]

# ------------------------
# EXTRA: Get user stats
# ------------------------
@app.get("/stats")
def get_stats():
    """Get statistics"""
    return {
        "total_users": len(users_db),
        "total_products": len(sample_products),
        "users_with_carts": len(carts_db),
        "total_cart_items": sum(len(cart) for cart in carts_db.values())}