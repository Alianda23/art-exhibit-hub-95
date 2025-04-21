
import os
import json
import http.server
import socketserver
import urllib.parse
import mimetypes
from http import HTTPStatus
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from decimal import Decimal

# Import modules
from auth import register_user, login_user, login_admin
from artwork import get_all_artworks, get_artwork, create_artwork, update_artwork, delete_artwork
from exhibition import get_all_exhibitions, get_exhibition, create_exhibition, update_exhibition, delete_exhibition
from contact import create_contact_message, get_messages, update_message, json_dumps
from db_setup import initialize_database
from middleware import auth_required, admin_required, extract_auth_token, verify_token
from mpesa import handle_stk_push_request, check_transaction_status, handle_mpesa_callback
from db_operations import get_all_tickets, get_all_orders

# Define the port
PORT = 8000

# Ensure the static/uploads directory exists
def ensure_uploads_directory():
    uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created directory: {uploads_dir}")

# Call this function to ensure directory exists
ensure_uploads_directory()

# Create a default exhibition image if it doesn't exist
def create_default_exhibition_image():
    default_image_path = os.path.join(os.path.dirname(__file__), "static", "uploads", "default_exhibition.jpg")
    if not os.path.exists(default_image_path):
        try:
            # Create a simple colored rectangle as the default image
            from shutil import copyfile
            
            # Copy a placeholder from public if it exists
            source_placeholder = os.path.join(os.path.dirname(__file__), "..", "public", "placeholder.svg")
            if os.path.exists(source_placeholder):
                copyfile(source_placeholder, default_image_path)
                print(f"Created default exhibition image from placeholder")
            else:
                # Create a simple file as fallback
                with open(default_image_path, "w") as f:
                    f.write("Default Exhibition Image")
                print(f"Created empty default exhibition image")
        except Exception as e:
            print(f"Failed to create default exhibition image: {e}")

# Call this function to ensure default exhibition image exists
create_default_exhibition_image()

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
            self._set_headers(404)
            self.wfile.write(b'File not found')
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
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
            
            elif self.path.startswith('/api/exhibitions/'):
                exhibition_id = self.path.split('/')[-1]
                auth_header = self.headers.get('Authorization')
                result = update_exhibition(auth_header, exhibition_id, data)
                self._send_response(result)
            
            elif self.path == '/api/contact':
                result = create_contact_message(data)
                self._send_response(result)
            
            elif self.path.startswith('/api/messages/'):
                message_id = self.path.split('/')[-1]
                auth_header = self.headers.get('Authorization')
                result = update_message(auth_header, message_id, data)
                self._send_response(result)
            
            elif self.path == '/api/mpesa/stkpush':
                result = handle_stk_push_request(data)
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
    
    def do_DELETE(self):
        if self.path.startswith('/api/artworks/'):
            artwork_id = self.path.split('/')[-1]
            auth_header = self.headers.get('Authorization')
            result = delete_artwork(auth_header, artwork_id)
            self._send_response(result)
        
        elif self.path.startswith('/api/exhibitions/'):
            exhibition_id = self.path.split('/')[-1]
            auth_header = self.headers.get('Authorization')
            result = delete_exhibition(auth_header, exhibition_id)
            self._send_response(result)
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run(server_class=http.server.HTTPServer, handler_class=APIHandler, port=PORT):
    # Initialize the database
    initialize_database()
    
    # Start the server
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

if __name__ == '__main__':
    run()
