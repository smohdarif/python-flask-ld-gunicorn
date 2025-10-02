# Gunicorn config file with LaunchDarkly post_fork hook

# Example worker settings (tweak for your needs)
workers = 2
threads = 1
bind = "0.0.0.0:8000"
timeout = 30

# Enhanced logging
loglevel = 'info'
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 60)
    server.log.info("MASTER PROCESS STARTING")
    server.log.info(f"Master PID: {server.pid}")
    server.log.info("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("=" * 60)
    server.log.info("SERVER READY - About to fork workers")
    server.log.info("=" * 60)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f">>> PRE-FORK: About to fork worker #{worker.age}")

def post_fork(server, worker):
    """
    Called after a worker is forked.
    
    NOTE: postfork() causes SIGSEGV crashes on macOS with LibreSSL.
    Instead, each worker initializes its own LaunchDarkly client.
    This is less efficient but stable and production-ready.
    """
    server.log.info(f"<<< POST-FORK: Worker {worker.pid} has been forked (without calling postfork)")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info(f"Worker {worker.pid} received interrupt signal")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exited")
