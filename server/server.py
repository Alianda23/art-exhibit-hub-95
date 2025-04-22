import os
import http.server
import json
import urllib.parse
from urllib.parse import urlparse
import mimetypes
from decimal import Decimal
from datetime import datetime
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_FILE = os.getenv("DATABASE_FILE") or 'database.db'

# Function to initialize the database
def initialize_database():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT
            )
        """)

        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)

        # Create artworks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                year INTEGER,
                description TEXT,
                image_url TEXT,
                price REAL NOT NULL,
                admin_id INTEGER,
                FOREIGN KEY (admin_id) REFERENCES admins (id)
            )
        """)

        # Create exhibitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exhibitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                price REAL NOT NULL,
                admin_id INTEGER,
                FOREIGN KEY (admin_id) REFERENCES admins (id)
            )
        """)

        # Create artwork_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artwork_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                artwork_id INTEGER,
                total_amount REAL NOT NULL,
                payment_status TEXT NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (artwork_id) REFERENCES artworks (id)
            )
        """)

        # Create exhibition_bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exhibition_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exhibition_id INTEGER,
                total_amount REAL NOT NULL,
                booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (exhibition_id) REFERENCES exhibitions (id)
            )
        """)

        # Create contact_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create mpesa_payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mpesa_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                phone_number TEXT NOT NULL,
                checkout_request_id TEXT UNIQUE,
                merchant_request_id TEXT,
                mpesa_receipt_number TEXT,
                transaction_date DATETIME,
                result_code INTEGER,
                result_desc TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()
        print("Database initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Function to get a database connection
def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- User Authentication ---
def register_user(name, email, password, phone):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",
                       (name, email, password, phone))
        conn.commit()
        user_id = cursor.lastrowid
        return {"message": "User registered successfully", "user_id": user_id}, 201
    except sqlite3.IntegrityError:
        return {"error": "Email already registered"}, 400
    except Exception as e:
        print(f"Registration error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def login_user(email, password):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, phone FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            user_dict = dict(user)
            return {"message": "Login successful", "user": user_dict}, 200
        else:
            return {"error": "Invalid credentials"}, 401
    except Exception as e:
        print(f"Login error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- Admin Authentication ---
def login_admin(email, password):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM admins WHERE email = ? AND password = ?", (email, password))
        admin = cursor.fetchone()
        if admin:
            admin_dict = dict(admin)
            return {"message": "Admin login successful", "admin": admin_dict}, 200
        else:
            return {"error": "Invalid credentials"}, 401
    except Exception as e:
        print(f"Admin login error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- Artwork Management ---
def create_artwork(auth_header, data):
    # Verify auth token
    if not auth_header:
        return {"error": "Authentication required"}, 401
    
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO artworks (title, artist, year, description, image_url, price, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data['title'], data['artist'], data.get('year'), data.get('description'), data.get('image_url'), data['price'], 1))  # Assuming admin_id is 1
        conn.commit()
        artwork_id = cursor.lastrowid
        return {"message": "Artwork created successfully", "artwork_id": artwork_id}, 201
    except Exception as e:
        print(f"Artwork creation error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def get_all_artworks():
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM artworks")
        artworks = [dict(row) for row in cursor.fetchall()]
        return {"artworks": artworks}, 200
    except Exception as e:
        print(f"Error getting artworks: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def get_artwork(artwork_id):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        artwork = cursor.fetchone()
        if artwork:
            return {"artwork": dict(artwork)}, 200
        else:
            return {"error": "Artwork not found"}, 404
    except Exception as e:
        print(f"Error getting artwork: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def update_artwork(auth_header, artwork_id, data):
    # Verify auth token
    if not auth_header:
        return {"error": "Authentication required"}, 401
    
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE artworks SET title = ?, artist = ?, year = ?, description = ?, image_url = ?, price = ?
            WHERE id = ?
        """, (data['title'], data['artist'], data.get('year'), data.get('description'), data.get('image_url'), data['price'], artwork_id))
        conn.commit()
        if cursor.rowcount > 0:
            return {"message": "Artwork updated successfully"}, 200
        else:
            return {"error": "Artwork not found"}, 404
    except Exception as e:
        print(f"Artwork update error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- Exhibition Management ---
def create_exhibition(auth_header, data):
    # Verify auth token
    if not auth_header:
        return {"error": "Authentication required"}, 401
    
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exhibitions (title, start_date, end_date, description, image_url, price, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data['title'], data['start_date'], data['end_date'], data.get('description'), data.get('image_url'), data['price'], 1))  # Assuming admin_id is 1
        conn.commit()
        exhibition_id = cursor.lastrowid
        return {"message": "Exhibition created successfully", "exhibition_id": exhibition_id}, 201
    except Exception as e:
        print(f"Exhibition creation error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def get_all_exhibitions():
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exhibitions")
        exhibitions = [dict(row) for row in cursor.fetchall()]
        return {"exhibitions": exhibitions}, 200
    except Exception as e:
        print(f"Error getting exhibitions: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def get_exhibition(exhibition_id):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exhibitions WHERE id = ?", (exhibition_id,))
        exhibition = cursor.fetchone()
        if exhibition:
            return {"exhibition": dict(exhibition)}, 200
        else:
            return {"error": "Exhibition not found"}, 404
    except Exception as e:
        print(f"Error getting exhibition: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- Ticket Management ---
def get_all_tickets():
    # Placeholder function - replace with actual implementation
    return {"message": "Tickets endpoint hit"}, 200

# --- Order Management ---
def get_all_orders():
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        
        # Fetch artwork orders
        cursor.execute("""
            SELECT o.id, o.user_id, u.name as user_name, o.artwork_id as reference_id, 
                   a.title as item_title, o.total_amount as amount, o.payment_status, 
                   'artwork' as type, o.order_date as created_at
            FROM artwork_orders o
            JOIN users u ON o.user_id = u.id
            LEFT JOIN artworks a ON o.artwork_id = a.id
            ORDER BY o.order_date DESC
        """)
        artwork_orders = []
        for row in cursor.fetchall():
            order = {}
            for i, col_name in enumerate(cursor.column_names):
                order[col_name] = row[i]
                if isinstance(order[col_name], Decimal):
                    order[col_name] = float(order[col_name])
            artwork_orders.append(order)
        
        # Fetch exhibition bookings
        cursor.execute("""
            SELECT b.id, b.user_id, u.name as user_name, b.exhibition_id as reference_id, 
                   e.title as item_title, b.total_amount as amount, b.status as payment_status, 
                   'exhibition' as type, b.booking_date as created_at
            FROM exhibition_bookings b
            JOIN users u ON b.user_id = u.id
            LEFT JOIN exhibitions e ON b.exhibition_id = e.id
            ORDER BY b.booking_date DESC
        """)
        exhibition_bookings = []
        for row in cursor.fetchall():
            booking = {}
            for i, col_name in enumerate(cursor.column_names):
                booking[col_name] = row[i]
                if isinstance(booking[col_name], Decimal):
                    booking[col_name] = float(booking[col_name])
            exhibition_bookings.append(booking)
        
        return {"orders": artwork_orders, "bookings": exhibition_bookings}, 200
    except Exception as e:
        print(f"Error getting all orders: {e}")
        return {"error": str(e)}, 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- Contact Messages ---
def create_contact_message(data):
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                       (data['name'], data['email'], data['message']))
        conn.commit()
        message_id = cursor.lastrowid
        return {"message": "Message created successfully", "message_id": message_id}, 201
    except Exception as e:
        print(f"Message creation error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- Messages ---
def get_messages(auth_header):
    # Verify auth token
    if not auth_header:
        return {"error": "Authentication required"}, 401
    
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
        messages = [dict(row) for row in cursor.fetchall()]
        return {"messages": messages}, 200
    except Exception as e:
        print(f"Error getting messages: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

def update_message(auth_header, message_id, data):
    # Verify auth token
    if not auth_header:
        return {"error": "Authentication required"}, 401
    
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}, 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET is_read = ? WHERE id = ?", (data['is_read'], message_id))
        conn.commit()
        if cursor.rowcount > 0:
            return {"message": "Message updated successfully"}, 200
        else:
            return {"error": "Message not found"}, 404
    except Exception as e:
        print(f"Message update error: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

# --- M-Pesa Integration ---
def handle_stk_push_request(data):
    # Placeholder function - replace with actual implementation
    return {"message": "STK push request received", "data": data}, 200

def handle_mpesa_callback(data):
    # Placeholder function - replace with actual implementation
    print("M-Pesa callback data:", data)
    return {"message": "M-Pesa callback received"}, 200

def check_transaction_status(checkout_request_id):
    # Placeholder function - replace with actual implementation
    return {"message": f"Transaction status for {checkout_request_id}"}, 200

def ensure_uploads_directory():
    uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created directory: {uploads_dir}")

# Call this function to ensure directory exists
ensure_uploads_directory()

# Create a default image if it doesn't exist
def create_default_image():
    default_image_path = os.path.join(os.path.dirname(__file__), "static", "uploads", "placeholder.jpg")
    if not os.path.exists(default_image_path):
        try:
            # Create a simple colored rectangle as the default image
            from PIL import Image, ImageDraw
            
            # Create a new image with a solid background
            img = Image.new('RGB', (600, 400), color=(200, 200, 200))
            d = ImageDraw.Draw(img)
            
            # Draw a placeholder rectangle
            d.rectangle([(50, 50), (550, 350)], outline=(100, 100, 100), width=2)
            d.text((300, 200), "No Image Available", fill=(100, 100, 100))
            
            img.save(default_image_path)
            print(f"Created default placeholder image at {default_image_path}")
        except Exception as e:
            print(f"Failed to create default image: {e}")
            # Fallback: Create a simple file
            with open(default_image_path, "w") as f:
                f.write("Default Image Placeholder")

# Try to create the default image
try:
    create_default_image()
except:
    print("Failed to create default image, continuing anyway")

# Ensure the public placeholder.svg is available
def create_placeholder_svg():
    placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
    if not os.path.exists(placeholder_path):
        try:
            svg_content = """<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
                <rect width="600" height="400" fill="#f0f0f0" />
                <text x="50%" y="50%" font-family="Arial" font-size="24" text-anchor="middle">Image Placeholder</text>
            </svg>"""
            with open(placeholder_path, "w") as f:
                f.write(svg_content)
            print(f"Created placeholder SVG at {placeholder_path}")
        except Exception as e:
            print(f"Failed to create placeholder SVG: {e}")

# Create placeholder SVG
create_placeholder_svg()

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

class APIHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def _parse_json_body(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode('utf-8'))
    
    def _send_response(self, data, status_code=200):
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, cls=DecimalEncoder).encode())
    
    def _serve_static_file(self, file_path):
        try:
            # Determine content type based on file extension
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            with open(file_path, 'rb') as file:
                self._set_headers(200, content_type)
                self.wfile.write(file.read())
        except FileNotFoundError:
            # Serve default placeholder instead
            placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
            if os.path.exists(placeholder_path):
                with open(placeholder_path, 'rb') as file:
                    self._set_headers(200, 'image/svg+xml')
                    self.wfile.write(file.read())
            else:
                self._set_headers(404)
                self.wfile.write(b'File not found')
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Special handling for placeholder.svg
        if path == '/placeholder.svg':
            placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.svg")
            return self._serve_static_file(placeholder_path)
        
        # Handle static files
        if path.startswith('/static/'):
            file_path = os.path.join(os.path.dirname(__file__), path[1:])  # Remove leading /
            return self._serve_static_file(file_path)
        
        # Handle API endpoints
        if path == '/api/artworks':
            result = get_all_artworks()
            self._send_response(result)
        
        elif path.startswith('/api/artworks/'):
            artwork_id = path.split('/')[-1]
            result = get_artwork(artwork_id)
            self._send_response(result)
        
        elif path == '/api/exhibitions':
            result = get_all_exhibitions()
            self._send_response(result)
        
        elif path.startswith('/api/exhibitions/'):
            exhibition_id = path.split('/')[-1]
            result = get_exhibition(exhibition_id)
            self._send_response(result)
        
        elif path == '/api/tickets':
            auth_header = self.headers.get('Authorization')
            result = get_all_tickets()
            self._send_response(result)
        
        elif path == '/api/orders':
            auth_header = self.headers.get('Authorization')
            result = get_all_orders()
            self._send_response(result)
        
        elif path.startswith('/api/users/') and '/orders' in path:
            auth_header = self.headers.get('Authorization')
            user_id = path.split('/')[3]  # Extract user_id from /api/users/{user_id}/orders
            
            # Verify auth token
            if not auth_header:
                self._send_response({"error": "Authentication required"}, 401)
                return
                
            # Connect to database and fetch orders for this user
            connection = get_db_connection()
            if connection is None:
                self._send_response({"error": "Database connection failed"}, 500)
                return
                
            try:
                cursor = connection.cursor()
                query = """
                SELECT o.id, o.user_id, u.name as user_name, o.artwork_id as reference_id, 
                       a.title as item_title, o.total_amount as amount, o.payment_status, 
                       'artwork' as type, o.order_date as created_at
                FROM artwork_orders o
                JOIN users u ON o.user_id = u.id
                LEFT JOIN artworks a ON o.artwork_id = a.id
                WHERE o.user_id = %s
                ORDER BY o.order_date DESC
                """
                
                cursor.execute(query, (user_id,))
                orders = []
                for row in cursor.fetchall():
                    order = {}
                    for i, col_name in enumerate(cursor.column_names):
                        order[col_name] = row[i]
                        if isinstance(order[col_name], Decimal):
                            order[col_name] = float(order[col_name])
                    orders.append(order)
                
                self._send_response({"orders": orders})
            except Exception as e:
                print(f"Error getting user orders: {e}")
                self._send_response({"error": str(e)}, 500)
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        
        elif path.startswith('/api/messages'):
            auth_header = self.headers.get('Authorization')
            result = get_messages(auth_header)
            self._send_response(result)
        
        elif path.startswith('/api/mpesa/status/'):
            checkout_request_id = path.split('/')[-1]
            result = check_transaction_status(checkout_request_id)
            self._send_response(result)
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                data = urllib.parse.parse_qs(post_data)
                # Convert lists to single values
                for key in data:
                    if isinstance(data[key], list) and len(data[key]) == 1:
                        data[key] = data[key][0]
            
            if self.path == '/api/register':
                result = register_user(
                    data.get('name'),
                    data.get('email'),
                    data.get('password'),
                    data.get('phone', '')
                )
                self._send_response(result)
            
            elif self.path == '/api/login':
                result = login_user(
                    data.get('email'),
                    data.get('password')
                )
                self._send_response(result)
            
            elif self.path == '/api/admin-login':
                result = login_admin(
                    data.get('email'),
                    data.get('password')
                )
                self._send_response(result)
            
            elif self.path == '/api/artworks':
                auth_header = self.headers.get('Authorization')
                result = create_artwork(auth_header, data)
                self._send_response(result)
            
            elif self.path.startswith('/api/artworks/'):
                artwork_id = self.path.split('/')[-1]
                auth_header = self.headers.get('Authorization')
                result = update_artwork(auth_header, artwork_id, data)
                self._send_response(result)
            
            elif self.path == '/api/exhibitions':
                auth_header = self.headers.get('Authorization')
                result = create_exhibition(auth_header, data)
                self._send_response(result)
            
            elif self.path == '/api/mpesa/stkpush':
                auth_header = self.headers.get('Authorization')
                result = handle_stk_push_request(data)
                self._send_response(result)
            
            elif self.path == '/api/contact':
                result = create_contact_message(data)
                self._send_response(result)
            
            elif self.path.startswith('/api/messages/'):
                message_id = self.path.split('/')[-1]
                auth_header = self.headers.get('Authorization')
                result = update_message(auth_header, message_id, data)
                self._send_response(result)
            
            elif self.path == '/api/mpesa/callback':
                result = handle_mpesa_callback(data)
                self._send_response(result)
            
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                
        except Exception as e:
            print(f"Error handling POST request: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_PUT(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/artworks/'):
            artwork_id = path.split('/')[-1]
            auth_header = self.headers.get('Authorization')
            result = update_artwork(auth_header, artwork_id, data)
            self._send_response(result)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/artworks/'):
            artwork_id = path.split('/')[-1]
            # Placeholder: Add authentication check here if needed
            
            conn = get_db_connection()
            if conn is None:
                self._send_response({"error": "Database connection failed"}, 500)
                return
            
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM artworks WHERE id = ?", (artwork_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    self._send_response({"message": "Artwork deleted successfully"}, 200)
                else:
                    self._send_response({"error": "Artwork not found"}, 404)
            except Exception as e:
                print(f"Artwork deletion error: {e}")
                self._send_response({"error": str(e)}, 500)
            finally:
                conn.close()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run(server_class=http.server.HTTPServer, handler_class=APIHandler, port=8000):
    server_address = ('', port)
