# Gunicorn config for Docker/Linux with LaunchDarkly postfork() best practice

# Worker settings
workers = 2
threads = 1
bind = "0.0.0.0:8000"
timeout = 30

# Enhanced logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 60)
    server.log.info("🐳 DOCKER: MASTER PROCESS STARTING")
    server.log.info(f"Master PID: {server.pid}")
    server.log.info("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("=" * 60)
    server.log.info("🐳 DOCKER: SERVER READY - About to fork workers")
    server.log.info("=" * 60)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f">>> PRE-FORK: About to fork worker #{worker.age}")

def post_fork(server, worker):
    """
    Called after a worker is forked.
    
    THIS USES LAUNCHDARKLY'S RECOMMENDED BEST PRACTICE!
    Reinitialize LaunchDarkly client threads in each worker process.
    Works in Docker/Linux with OpenSSL.
    """
    server.log.info(f"<<< POST-FORK: Worker {worker.pid} has been forked!")
    
    import ldclient
    try:
        server.log.info(f"🔧 Worker {worker.pid}: Getting LaunchDarkly client...")
        client = ldclient.get()
        
        if hasattr(client, 'postfork'):
            server.log.info(f"🚀 Worker {worker.pid}: Calling client.postfork()...")
            client.postfork()
            server.log.info(f"✅ Worker {worker.pid}: LaunchDarkly postfork() completed successfully!")
            server.log.info(f"   This is LaunchDarkly's BEST PRACTICE!")
        else:
            server.log.warning(f"⚠️  Worker {worker.pid}: LaunchDarkly client doesn't have postfork() method")
    except Exception as e:
        server.log.error(f"❌ Worker {worker.pid}: LaunchDarkly postfork() failed: {e}")
        import traceback
        server.log.error(traceback.format_exc())

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exited") 