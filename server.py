import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))

# go to project directory explicitly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReusableTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving UI on port {PORT}")
    httpd.serve_forever()
