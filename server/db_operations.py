
from database import get_db_connection
from decimal import Decimal
import random
import string
import json

def generate_ticket_code():
    """Generate a unique ticket code"""
    prefix = 'TKT'
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{random_chars}"

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def create_order(user_id, order_type, reference_id, amount):
    """Create a new order in the database - uses the appropriate order table based on type"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Use the appropriate table based on order type
        if order_type == 'artwork':
            query = """
            INSERT INTO artwork_orders (user_id, artwork_id, total_amount, name, email, phone, delivery_address, payment_method, payment_status)
            SELECT %s, %s, %s, u.name, u.email, u.phone, '', 'mpesa', 'pending'
            FROM users u WHERE u.id = %s
            """
            cursor.execute(query, (user_id, reference_id, amount, user_id))
            order_id = cursor.lastrowid
        elif order_type == 'exhibition':
            query = """
            INSERT INTO exhibition_bookings (user_id, exhibition_id, slots, name, email, phone, payment_method, payment_status, total_amount)
            SELECT %s, %s, 1, u.name, u.email, u.phone, 'mpesa', 'pending', %s
            FROM users u WHERE u.id = %s
            """
            cursor.execute(query, (user_id, reference_id, amount, user_id))
            order_id = cursor.lastrowid
        else:
            return {"error": "Invalid order type"}
            
        connection.commit()
        
        return {"success": True, "order_id": order_id}
    except Exception as e:
        print(f"Error creating order: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_ticket(user_id, exhibition_id, slots):
    """Create a new ticket in the exhibition_bookings table"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Check if the booking exists
        query = """
        SELECT id, ticket_code FROM exhibition_bookings
        WHERE user_id = %s AND exhibition_id = %s AND payment_status = 'completed'
        """
        cursor.execute(query, (user_id, exhibition_id))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            booking_id = existing_booking[0]
            ticket_code = existing_booking[1]
        else:
            # Generate a ticket code
            ticket_code = generate_ticket_code()
            
            # Update existing booking with ticket code if pending payment
            query = """
            UPDATE exhibition_bookings 
            SET ticket_code = %s
            WHERE user_id = %s AND exhibition_id = %s AND ticket_code IS NULL
            """
            cursor.execute(query, (ticket_code, user_id, exhibition_id))
            
            if cursor.rowcount == 0:
                # Create a new booking record
                query = """
                INSERT INTO exhibition_bookings (user_id, exhibition_id, slots, ticket_code, name, email, phone, payment_method, payment_status, total_amount)
                SELECT %s, %s, %s, %s, name, email, phone, 'mpesa', 'pending', 
                (SELECT ticket_price FROM exhibitions WHERE id = %s) * %s
                FROM users WHERE id = %s
                """
                cursor.execute(query, (user_id, exhibition_id, slots, ticket_code, exhibition_id, slots, user_id))
                
            booking_id = cursor.lastrowid
            
        connection.commit()
        
        return {"success": True, "booking_id": booking_id, "ticket_code": ticket_code}
    except Exception as e:
        print(f"Error creating ticket: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_all_orders():
    """Get all artwork orders from the database"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Get all artwork orders
        query = """
        SELECT o.id, o.user_id, u.name as user_name, o.artwork_id as reference_id, 
               a.title as item_title, o.total_amount as amount, o.payment_status, 
               'artwork' as type, o.order_date as created_at
        FROM artwork_orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN artworks a ON o.artwork_id = a.id
        ORDER BY o.order_date DESC
        """
        cursor.execute(query)
        orders = []
        for row in cursor.fetchall():
            order = {}
            for i, col_name in enumerate(cursor.column_names):
                order[col_name] = row[i]
                if isinstance(order[col_name], Decimal):
                    order[col_name] = float(order[col_name])
            orders.append(order)
        
        # Convert to JSON and back to handle Decimal types
        orders_json = json.dumps(orders, cls=DecimalEncoder)
        return {"orders": json.loads(orders_json)}
    except Exception as e:
        print(f"Error getting orders: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_all_tickets():
    """Get all exhibition bookings (tickets) from database"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Get all exhibition bookings
        query = """
        SELECT b.id, b.user_id, u.name as user_name, b.exhibition_id, e.title as exhibition_title,
               e.image_url as exhibition_image_url, b.ticket_code, b.slots, 
               b.booking_date, b.payment_status as status, b.total_amount
        FROM exhibition_bookings b
        JOIN users u ON b.user_id = u.id
        JOIN exhibitions e ON b.exhibition_id = e.id
        ORDER BY b.booking_date DESC
        """
        cursor.execute(query)
        tickets = []
        for row in cursor.fetchall():
            ticket = {}
            for i, col_name in enumerate(cursor.column_names):
                ticket[col_name] = row[i]
                if isinstance(ticket[col_name], Decimal):
                    ticket[col_name] = float(ticket[col_name])
            tickets.append(ticket)
        
        # Convert to JSON and back to handle Decimal types
        tickets_json = json.dumps(tickets, cls=DecimalEncoder)
        return {"tickets": json.loads(tickets_json)}
    except Exception as e:
        print(f"Error getting tickets: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_orders(user_id):
    """Get all orders and bookings for a specific user"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # Get artwork orders
        artwork_query = """
        SELECT o.id, o.user_id, o.artwork_id as reference_id, 
               a.title as item_title, o.total_amount as amount, o.payment_status, 
               'artwork' as type, o.order_date as created_at
        FROM artwork_orders o
        LEFT JOIN artworks a ON o.artwork_id = a.id
        WHERE o.user_id = %s
        ORDER BY o.order_date DESC
        """
        cursor.execute(artwork_query, (user_id,))
        artwork_orders = []
        for row in cursor.fetchall():
            order = {}
            for i, col_name in enumerate(cursor.column_names):
                order[col_name] = row[i]
                if isinstance(order[col_name], Decimal):
                    order[col_name] = float(order[col_name])
            artwork_orders.append(order)
        
        # Get exhibition bookings
        exhibition_query = """
        SELECT b.id, b.user_id, b.exhibition_id as reference_id, 
               e.title as item_title, b.total_amount as amount, b.payment_status, 
               'exhibition' as type, b.booking_date as created_at
        FROM exhibition_bookings b
        LEFT JOIN exhibitions e ON b.exhibition_id = e.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
        """
        cursor.execute(exhibition_query, (user_id,))
        exhibition_bookings = []
        for row in cursor.fetchall():
            booking = {}
            for i, col_name in enumerate(cursor.column_names):
                booking[col_name] = row[i]
                if isinstance(booking[col_name], Decimal):
                    booking[col_name] = float(booking[col_name])
            exhibition_bookings.append(booking)
        
        # Convert to JSON and back to handle Decimal types
        orders_json = json.dumps(artwork_orders, cls=DecimalEncoder)
        bookings_json = json.dumps(exhibition_bookings, cls=DecimalEncoder)
        
        return {
            "orders": json.loads(orders_json),
            "bookings": json.loads(bookings_json)
        }
    except Exception as e:
        print(f"Error getting user orders: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
