import os
import socket
import threading
import queue
import logging
from datetime import datetime
from urllib.parse import unquote
from functools import lru_cache

# Configuration
HOST = '127.0.0.1'  # IP address where the server will run
PORT = 8080  # Port number where the server will listen for connections
STATIC_DIR = 'static'  # Directory containing static files to be served
LOG_FILE = 'server.log'  # File for logging server activity
THREAD_POOL_SIZE = 4  # Number of worker threads in the thread pool
MAX_QUEUE_SIZE = 10  # Maximum size of the request queue
CACHE_SIZE = 1  # Maximum number of files to cache in memory
REQUEST_QUEUE = queue.Queue(MAX_QUEUE_SIZE)  # Thread-safe queue for client requests
CACHE_ENABLED = True  # Toggle caching on or off

# Thread-safe locks
LOG_LOCK = threading.Lock()  # Lock for safely logging messages

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,  # Log file path
    level=logging.INFO,  # Logging level
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log message format
)

def log_message(message):
    """Logs a message safely."""
    logging.info(message)  # Logs the given message to the log file

def load_file(file_path):
    """Loads a file from disk, optionally caching the result."""
    if CACHE_ENABLED:
        return _load_file_cached(file_path)  # Use the cached version
    else:
        return _load_file_uncached(file_path)  # Direct file loading

@lru_cache(maxsize=CACHE_SIZE)
def _load_file_cached(file_path):
    """Cached file loader."""
    with open(file_path, 'rb') as f:
        return f.read()

def _load_file_uncached(file_path):
    """Direct file loader (no caching)."""
    with open(file_path, 'rb') as f:
        return f.read()

def handle_client(client_socket, client_address):
    """Handles individual client requests."""
    try:
        request = client_socket.recv(1024).decode('utf-8')  # Read the HTTP request from the client
        if not request:  # If the request is empty, return
            return

        request_line = request.splitlines()[0]  # Extract the first line of the HTTP request
        method, path, _ = request_line.split()  # Parse the HTTP method and path
        path = unquote(path)  # Decode URL-encoded characters in the path

        # Toggle cache endpoint
        if path == '/toggle_cache':
            global CACHE_ENABLED
            CACHE_ENABLED = not CACHE_ENABLED  # Toggle cache
            response = f"HTTP/1.1 200 OK\r\n\r\nCache is now {'enabled' if CACHE_ENABLED else 'disabled'}."
            client_socket.sendall(response.encode('utf-8'))
            log_message(f"Cache toggled: {'enabled' if CACHE_ENABLED else 'disabled'}")
            return

        # Only GET method is allowed
        if method != 'GET':
            response = "HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed"
            client_socket.sendall(response.encode('utf-8'))
            log_message(f"405 Method Not Allowed: {method} {path}")
            return

        if path == '/':  # Default to serving the index.html file
            path = '/index.html'

        file_path = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip('/')))  # Resolve file path
        if not file_path.startswith(STATIC_DIR) or not os.path.exists(file_path) or os.path.isdir(file_path):
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile Not Found"
            client_socket.sendall(response.encode('utf-8'))
            log_message(f"404 Not Found: {file_path}")
            return

        content = load_file(file_path)  # Load the file content (may be cached)
        response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n"
        client_socket.sendall(response.encode('utf-8') + content)
        log_message(f"200 OK: {file_path}")

    except Exception as e:
        log_message(f"Error handling request from {client_address}: {e}")
    finally:
        client_socket.close()

def worker_thread():
    """Worker thread to process queued requests."""
    while True:
        client_socket, client_address = REQUEST_QUEUE.get()  # Get the next request from the queue
        if client_socket is None:  # Exit signal for the thread
            break
        try:
            handle_client(client_socket, client_address)  # Process the client request
        except Exception as e:
            log_message(f"Error in worker thread: {e}")
        REQUEST_QUEUE.task_done()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server started at http://{HOST}:{PORT}")
    log_message(f"Server started at http://{HOST}:{PORT}")

    # Create and start worker threads
    threads = []
    for _ in range(THREAD_POOL_SIZE):
        thread = threading.Thread(target=worker_thread, daemon=True)
        threads.append(thread)
        thread.start()

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            log_message(f"Connection accepted from {client_address}")
            try:
                REQUEST_QUEUE.put((client_socket, client_address), timeout=5)
            except queue.Full:
                log_message(f"Request from {client_address} rejected: Queue full")
                client_socket.close()
    except KeyboardInterrupt:
        log_message("Server shutting down...")
    finally:
        for _ in range(THREAD_POOL_SIZE):
            REQUEST_QUEUE.put((None, None))
        for thread in threads:
            thread.join()
        server_socket.close()
        log_message("Server stopped.")

if __name__ == "__main__":
    main()
