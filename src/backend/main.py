"""Compatibility entrypoint for gunicorn: main:app"""
from app import app

if __name__ == "__main__":
    import os
    PORT = int(os.getenv('PORT', 8000))
    print(f"📡 Flask Bookstore Backend listening on 0.0.0.0:{PORT}", flush=True)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
