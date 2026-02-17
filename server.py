from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os

PORT = int(os.environ.get("PORT", 8080))

Handler = SimpleHTTPRequestHandler

with TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print("Server running on port", PORT)
    httpd.serve_forever()
