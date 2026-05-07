#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

BOOKS = [
    {"id": "1", "title": "Cloud Native Patterns", "author": "Cornelia Davis"},
    {"id": "2", "title": "Kubernetes in Action", "author": "Marko Luksa"},
    {"id": "3", "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"}
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if self.path == '/healthz':
            data = {"status": "healthy", "service": "backend"}
        elif self.path == '/ready':
            data = {"status": "ready", "service": "backend"}
        elif self.path == '/api/books':
            data = {"books": BOOKS, "count": len(BOOKS)}
        elif self.path.startswith('/api/books/'):
            book_id = self.path.split('/')[-1]
            book = next((b for b in BOOKS if b["id"] == book_id), None)
            data = book or {"error": "not found"}
        else:
            data = {"error": "not found"}
        self.wfile.write(json.dumps(data).encode())
    def log_message(self, *args): pass

if __name__ == "__main__":
    HTTPServer(('0.0.0.0', 8000), Handler).serve_forever()