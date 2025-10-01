# Gunicorn config file with LaunchDarkly post_fork hook

# Example worker settings (tweak for your needs)
workers = 2
threads = 1
bind = "0.0.0.0:8000"
timeout = 30

def post_fork(server, worker):
    """
    Called after a worker is forked.
    Reinitialize LaunchDarkly client threads in each worker process.
    """
    import ldclient
    try:
        client = ldclient.get()
        if hasattr(client, 'postfork'):
            client.postfork()
            server.log.info(f"LaunchDarkly postfork() completed in worker {worker.pid}")
        else:
            server.log.warning(f"LaunchDarkly client doesn't have postfork() method")
    except Exception as e:
        server.log.error(f"LaunchDarkly postfork() failed in worker {worker.pid}: {e}")
