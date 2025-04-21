
# ... keep existing code (imports and initial setup)

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
    # ... keep existing code (handler methods)
    
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
    
    # ... keep existing code (do_POST method)
    
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
        # ... keep existing code
        pass
    
    def do_DELETE(self):
        # ... keep existing code
        pass

def run(server_class=http.server.HTTPServer, handler_class=APIHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    try:
        # Initialize database
        if not initialize_database():
            print("Warning: Database initialization had issues")
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server")
        httpd.server_close()

if __name__ == "__main__":
    run()
