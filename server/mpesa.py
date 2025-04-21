
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
    except Error as e:
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
