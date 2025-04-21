
# M-Pesa API utilities

# M-Pesa credentials
import os
import json
import requests
import base64
import datetime
from decimal import Decimal
from database import get_db_connection

# M-Pesa API configuration
CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', 'sMwMwGZ8oOiSkNrUIrPbcCeWIO8UiQ3SV4CyX739uAyZVs1F')
CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', 'A3Hs5zRY3nDCn7XpxPuc1iAKpfy6UDdetiCalIAfuAIpgTROI5yCqqOewDfThh2o')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', 'your_passkey')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')  # Default is Safaricom test shortcode
CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'https://webhook.site/3c1f62b5-4214-47d6-9f26-71c1f4b9c8f0')
API_BASE_URL = "https://sandbox.safaricom.co.ke"

# Function to initiate STK Push
def initiate_stk_push(phone_number, amount, account_reference, order_type, order_id, user_id):
    """Simulate initiating an STK push"""
    print(f"Initiating STK Push for {phone_number}, amount: {amount}, order: {order_type}-{order_id}")
    
    # Generate unique transaction ID for this request
    checkout_request_id = f"ws_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{order_id}"
    merchant_request_id = f"mr_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{order_id}"
    
    # Save the transaction details to the database
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        # First, check if the order exists in the appropriate table
        if order_type == "artwork":
            query = """
            SELECT id, payment_status FROM artwork_orders
            WHERE id = %s AND user_id = %s
            """
        elif order_type == "exhibition":
            query = """
            SELECT id, payment_status FROM exhibition_bookings
            WHERE id = %s AND user_id = %s
            """
        else:
            return {"error": "Invalid order type"}
            
        cursor.execute(query, (order_id, user_id))
        order = cursor.fetchone()
        
        if not order:
            # Create the order if it doesn't exist
            from db_operations import create_order, create_ticket
            
            if order_type == "artwork":
                result = create_order(user_id, order_type, order_id, amount)
                if "error" in result:
                    return result
            elif order_type == "exhibition":
                # For exhibition, we assume slots = 1 if not specified
                slots = 1
                result = create_ticket(user_id, order_id, slots)
                if "error" in result:
                    return result
        
        # Insert MPesa transaction record
        query = """
        INSERT INTO mpesa_transactions 
        (checkout_request_id, merchant_request_id, order_type, order_id, user_id, amount, phone_number, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
        """
        cursor.execute(query, (
            checkout_request_id,
            merchant_request_id,
            order_type,
            order_id,
            user_id,
            amount,
            phone_number
        ))
        connection.commit()
        
        # For demonstration/development, simulate successful transaction
        # In production, this would be handled by the MPesa callback
        if True:  # Always succeed in demo
            # Simulate a successful payment after a short delay
            # In production, this would be handled by the callback
            update_order_status(order_type, order_id, "completed")
            
            # Update the transaction status
            query = """
            UPDATE mpesa_transactions
            SET status = 'completed', result_code = '0', result_desc = 'Success'
            WHERE checkout_request_id = %s
            """
            cursor.execute(query, (checkout_request_id,))
            connection.commit()
        
        return {
            "success": True,
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id,
            "phone_number": phone_number,
            "amount": amount
        }
    except Exception as e:
        print(f"Error initiating STK push: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def check_transaction_status(checkout_request_id):
    """Check the status of an MPesa transaction"""
    connection = get_db_connection()
    if connection is None:
        return {"error": "Database connection failed"}
    
    cursor = connection.cursor()
    
    try:
        query = """
        SELECT status, result_code, result_desc, order_type, order_id
        FROM mpesa_transactions
        WHERE checkout_request_id = %s
        """
        cursor.execute(query, (checkout_request_id,))
        result = cursor.fetchone()
        
        if not result:
            return {"error": "Transaction not found"}
        
        status, result_code, result_desc, order_type, order_id = result
        
        return {
            "success": True,
            "checkout_request_id": checkout_request_id,
            "status": status,
            "result_code": result_code,
            "result_desc": result_desc,
            "order_type": order_type,
            "order_id": order_id
        }
    except Exception as e:
        print(f"Error checking transaction status: {e}")
        return {"error": str(e)}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def handle_mpesa_callback(callback_data):
    """Handle callback from MPesa API"""
    print(f"MPesa callback received: {callback_data}")
    
    try:
        # Extract transaction details from callback
        body = callback_data.get("Body", {})
        stkCallback = body.get("stkCallback", {})
        
        checkout_request_id = stkCallback.get("CheckoutRequestID")
        merchant_request_id = stkCallback.get("MerchantRequestID")
        result_code = stkCallback.get("ResultCode")
        result_desc = stkCallback.get("ResultDesc")
        
        # Get transaction details from database
        connection = get_db_connection()
        if connection is None:
            return {"error": "Database connection failed"}
        
        cursor = connection.cursor()
        
        try:
            # Get transaction details
            query = """
            SELECT order_type, order_id, status
            FROM mpesa_transactions
            WHERE checkout_request_id = %s
            """
            cursor.execute(query, (checkout_request_id,))
            result = cursor.fetchone()
            
            if not result:
                return {"error": "Transaction not found"}
            
            order_type, order_id, current_status = result
            
            # If transaction is already completed, just return success
            if current_status == 'completed':
                return {"success": True, "message": "Transaction already processed"}
            
            # Update transaction status based on result code
            status = 'completed' if result_code == '0' else 'failed'
            
            query = """
            UPDATE mpesa_transactions
            SET status = %s, result_code = %s, result_desc = %s
            WHERE checkout_request_id = %s
            """
            cursor.execute(query, (status, result_code, result_desc, checkout_request_id))
            connection.commit()
            
            # If payment was successful, update order status
            if result_code == '0':
                update_order_status(order_type, order_id, "completed")
            
            return {
                "success": True,
                "checkout_request_id": checkout_request_id,
                "status": status
            }
        except Exception as e:
            print(f"Error processing MPesa callback: {e}")
            return {"error": str(e)}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        print(f"Error handling MPesa callback: {e}")
        return {"error": str(e)}

# We need to modify the update_order_status function to use the correct tables
def update_order_status(order_type, order_id, payment_status):
    """Update order payment status in database"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    try:
        if order_type == "artwork":
            query = """
            UPDATE artwork_orders
            SET payment_status = %s
            WHERE id = %s
            """
        elif order_type == "exhibition":
            query = """
            UPDATE exhibition_bookings
            SET payment_status = %s
            WHERE id = %s
            """
        else:
            return False
        
        cursor.execute(query, (payment_status, order_id))
        connection.commit()
        
        # If it's an artwork order and payment is completed, update artwork status
        if order_type == "artwork" and payment_status == "completed":
            query = """
            UPDATE artworks a
            JOIN artwork_orders o ON a.id = o.artwork_id
            SET a.status = 'sold'
            WHERE o.id = %s
            """
            cursor.execute(query, (order_id,))
            connection.commit()
        
        # If it's an exhibition booking and payment is completed, update available slots
        if order_type == "exhibition" and payment_status == "completed":
            query = """
            UPDATE exhibitions e
            JOIN exhibition_bookings b ON e.id = b.exhibition_id
            SET e.available_slots = e.available_slots - b.slots
            WHERE b.id = %s
            """
            cursor.execute(query, (order_id,))
            connection.commit()
        
        return True
    except Exception as e:
        print(f"Error updating order: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Update the handle_stk_push_request function to work with correct tables
def handle_stk_push_request(request_data):
    """Handle STK Push request from frontend"""
    try:
        print("STK Push request received:", request_data)
        
        phone_number = request_data.get("phoneNumber")
        amount = request_data.get("amount")
        order_type = request_data.get("orderType")
        order_id = request_data.get("orderId")
        user_id = request_data.get("userId")
        account_reference = request_data.get("accountReference")
        callback_url = request_data.get("callbackUrl", CALLBACK_URL)
        slots = request_data.get("slots", 1)  # For exhibition tickets
        
        # Validate required fields
        required_fields = ["phoneNumber", "amount", "orderType", "orderId", "userId"]
        missing_fields = []
        
        for field in required_fields:
            value = request_data.get(field)
            if not value or (isinstance(value, str) and value.strip() == ''):
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(error_msg)
            return {"error": error_msg}
        
        # Initialize STK Push
        stk_result = initiate_stk_push(
            phone_number, 
            amount, 
            account_reference or f"{order_type}-{order_id}", 
            order_type, 
            order_id, 
            user_id
        )
        
        if "error" in stk_result:
            return stk_result
        
        # For development, create order and ticket immediately after STK push initiation
        from db_operations import create_ticket, create_order
        
        if order_type == "exhibition":
            # Create ticket
            ticket_result = create_ticket(user_id, order_id, slots)
            if "error" in ticket_result:
                return ticket_result
            
            return {
                "success": True,
                "message": "Exhibition ticket created successfully",
                "ticket": ticket_result,
                "stk": stk_result
            }
        elif order_type == "artwork":
            # Create order for artwork
            order_result = create_order(user_id, "artwork", order_id, amount)
            if "error" in order_result:
                return order_result
            
            return {
                "success": True,
                "message": "Artwork order created successfully",
                "order": order_result,
                "stk": stk_result
            }
        else:
            return {"error": "Invalid order type"}
    except Exception as e:
        print(f"Error handling STK Push request: {e}")
        return {"error": str(e)}
