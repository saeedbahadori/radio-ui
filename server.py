import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving UI on port {PORT}")
    httpd.serve_forever()
