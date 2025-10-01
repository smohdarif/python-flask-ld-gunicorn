# Flask + LaunchDarkly + Gunicorn

A simple Flask application integrated with LaunchDarkly feature flags, configured to run with Gunicorn using the `post_fork()` hook for optimal performance.

## Setup

### 1. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file with your LaunchDarkly SDK key:
```env
LAUNCHDARKLY_SDK_KEY=sdk-your-key-here
LD_FLAG_KEY=sample-flag
```

## Running the Application

### With Gunicorn (Production - with post_fork)
```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py --preload app:app
```

**Why use `--preload` with `post_fork()`?**

1. **Memory Efficiency**: The LaunchDarkly client is initialized once in the master process before forking workers
2. **Proper Threading**: `post_fork()` reinitializes threads/connections in each worker process after forking
3. **Best Practice**: This is the recommended way to use LaunchDarkly with Gunicorn

### Without preload (simpler, but less efficient)
```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py app:app
```

### With Flask development server (Development only)
```bash
source venv/bin/activate
FLASK_APP=app.py flask run --port 8000
```

## Endpoints

- `GET /` - Health check endpoint
- `GET /flag` - Evaluate a LaunchDarkly feature flag

Example response from `/flag`:
```json
{
  "flag": "sample-flag",
  "value": false,
  "initialized": true
}
```

## How post_fork() Works

### The Flow:

1. **Master Process Initialization** (with `--preload`):
   - Gunicorn loads `app.py` in the master process
   - LaunchDarkly client is initialized once: `ldclient.set_config(LDConfig(SDK_KEY))`
   - Client connects to LaunchDarkly and downloads feature flags

2. **Worker Forking**:
   - Gunicorn forks worker processes from the master
   - Each worker inherits the LaunchDarkly client state
   - **Problem**: Threads and network connections don't survive forking

3. **post_fork() Hook** (in `gunicorn.conf.py`):
   - Called automatically in each worker after forking
   - Calls `client.postfork()` to reinitialize:
     - Background threads for streaming updates
     - Event processing threads
     - Network connections

### Benefits:

✅ **Faster startup** - Flag data already loaded before forking  
✅ **Lower memory** - Shared read-only memory between workers  
✅ **Proper threading** - Each worker has its own threads  
✅ **Real-time updates** - Workers can receive live flag changes  

## Configuration

See `gunicorn.conf.py` for:
- Worker settings (currently 2 workers)
- Bind address (0.0.0.0:8000)
- post_fork() hook implementation

## Stopping the Server

```bash
pkill -9 gunicorn
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Gunicorn Master Process (--preload)    │
│  ┌───────────────────────────────────┐  │
│  │ LaunchDarkly Client Initialized   │  │
│  │ (flags downloaded, config loaded) │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ fork()
               ├──────────────┬──────────────┐
               ▼              ▼              ▼
         ┌─────────┐    ┌─────────┐   ┌─────────┐
         │Worker 1 │    │Worker 2 │   │Worker N │
         │postfork()    │postfork()   │postfork()
         └─────────┘    └─────────┘   └─────────┘
         Each worker reinitializes threads
``` 