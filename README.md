# Web Server Model

A lightweight, multi-threaded HTTP server capable of handling HTTP GET requests, serving static files, and logging server activity. The project demonstrates core operating system concepts, such as threads, mutexes, and socket programming.

## Features

1. **Static File Serving**  
   - Handles valid file requests (`HTTP 200 OK`).  
   - Responds with `HTTP 404 Not Found` or `HTTP 405 Method Not Allowed` as needed.

2. **Multithreading**  
   - Utilizes a thread pool for efficient handling of concurrent client requests.

3. **Caching**  
   - Implements in-memory caching to improve response times by reducing file system reads.

4. **Request Queuing**  
   - Queues incoming client requests to prevent overloading worker threads.

5. **Metrics Tracking**  
   - Logs successful, failed, and rejected requests for analysis.

6. **Thread-Safe Logging**  
   - Ensures safe and accurate server activity logging.

## Architecture

The server employs a modular architecture:  
- **Main Server Loop**: Accepts and queues client requests.  
- **Worker Threads**: Processes requests and generates responses.  
- **Cache Module**: Stores frequently accessed files for optimized performance.  
- **Metrics & Logging**: Tracks and logs server activity in a thread-safe manner.

## Technologies Used

- **Programming Language**: C++  
- **Key Concepts**: Threads, mutexes, sockets, and file I/O.

## Testing Scenarios

1. **Normal Load**: 100 requests with no simulated failures.  
2. **High Load**: 500 requests with a small thread pool to evaluate queuing.  
3. **Failure Simulation**: Timeout and connection errors to ensure proper handling.

### Observations
- Multithreading efficiently handled concurrent requests.  
- Caching improved response times for frequently accessed files.  
- Request queuing prevented server crashes under high load.  
- Error handling properly categorized failed and rejected requests.

## Conclusion

This project showcases the development of a robust, multi-threaded HTTP server with effective caching, request management, and logging mechanisms, tested under real-world conditions.
