# Running with LaunchDarkly's Best Practice (Docker)

## Why Docker?

LaunchDarkly's `postfork()` best practice **CANNOT work on macOS** with LibreSSL. 

**Docker provides a Linux environment with OpenSSL**, making `postfork()` stable.

---

## Quick Start

### 1. Update gunicorn.conf.py for Docker

The current `gunicorn.conf.py` has `postfork()` disabled for macOS compatibility.

For Docker (Linux with OpenSSL), restore the `postfork()` call:

```python
def post_fork(server, worker):
    """
    Called after a worker is forked.
    Reinitialize LaunchDarkly client threads in each worker process.
    """
    server.log.info(f"<<< POST-FORK: Worker {worker.pid} has been forked!")
    
    import ldclient
    try:
        server.log.info(f"Worker {worker.pid}: Calling ldclient.get()...")
        client = ldclient.get()
        
        if hasattr(client, 'postfork'):
            server.log.info(f"Worker {worker.pid}: Calling client.postfork()...")
            client.postfork()
            server.log.info(f"✅ Worker {worker.pid}: LaunchDarkly postfork() completed!")
        else:
            server.log.warning(f"⚠️  Worker {worker.pid}: No postfork() method")
    except Exception as e:
        server.log.error(f"❌ Worker {worker.pid}: postfork() failed: {e}")
```

### 2. Build and Run

```bash
# Build the Docker image
docker-compose build

# Run the app
docker-compose up
```

### 3. Test

```bash
curl http://localhost:8000/
curl http://localhost:8000/flag
```

---

## Expected Logs (With Docker)

```
[INFO] MASTER PROCESS STARTING
[INFO] Master PID: 7
🚀 [PID 7] Initializing LaunchDarkly client in master process...
✅ [PID 7] LaunchDarkly client initialized

[INFO] SERVER READY - About to fork workers
[INFO] >>> PRE-FORK: About to fork worker #0
[INFO] Booting worker with pid: 8

[INFO] <<< POST-FORK: Worker 8 has been forked!
[INFO] Worker 8: Calling ldclient.get()...
[INFO] Worker 8: Calling client.postfork()...
✅ Worker 8: LaunchDarkly postfork() completed!

[INFO] >>> PRE-FORK: About to fork worker #1
[INFO] Booting worker with pid: 9

[INFO] <<< POST-FORK: Worker 9 has been forked!
[INFO] Worker 9: Calling ldclient.get()...
[INFO] Worker 9: Calling client.postfork()...
✅ Worker 9: LaunchDarkly postfork() completed!
```

**✅ NO SIGSEGV crashes!**

---

## Comparison

| Environment | postfork() | Stability | Why |
|------------|------------|-----------|-----|
| **macOS (native)** | ❌ Crashes | ❌ SIGSEGV | LibreSSL incompatible |
| **macOS (Docker)** | ✅ Works | ✅ Stable | Linux + OpenSSL |
| **Linux Server** | ✅ Works | ✅ Stable | Native OpenSSL |

---

## For Development on Mac

### Option 1: Docker (Best Practice)
```bash
docker-compose up
```
✅ Uses LaunchDarkly's recommended approach
✅ Matches production environment

### Option 2: Native (Current - No postfork)
```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py app:app
```
✅ Works natively on Mac
❌ Doesn't use `postfork()` best practice
❌ Higher memory usage

---

## For Production

Always use Linux with OpenSSL:
- ✅ Docker containers
- ✅ AWS EC2 (Amazon Linux)
- ✅ Google Cloud (Ubuntu)
- ✅ Kubernetes
- ✅ Any Linux server

**With `--preload` and `postfork()`** for optimal performance. 