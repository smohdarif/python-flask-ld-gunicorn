# Expected Logs - Gunicorn Fork Process

When you run `./start_with_logs.sh` or `gunicorn --config gunicorn.conf.py --preload app:app`, you'll see the following sequence:

## 1. Master Process Initialization

```
[2025-10-01 17:41:09] [39430] [INFO] Starting gunicorn 23.0.0
[2025-10-01 17:41:09] [39430] [INFO] ============================================================
[2025-10-01 17:41:09] [INFO] MASTER PROCESS STARTING
[2025-10-01 17:41:09] [INFO] Master PID: 39430
[2025-10-01 17:41:09] [INFO] ============================================================
```

## 2. LaunchDarkly Client Initialization (Master Process - with --preload)

```
🚀 [PID 39430] Initializing LaunchDarkly client in master process...
✅ [PID 39430] LaunchDarkly client initialized, is_initialized=True
```

**KEY POINT**: This happens ONCE in the master process before any workers are forked!

## 3. Server Ready

```
[2025-10-01 17:41:09] [INFO] Listening at: http://0.0.0.0:8000 (39430)
[2025-10-01 17:41:09] [INFO] Using worker: sync
[2025-10-01 17:41:09] [INFO] ============================================================
[2025-10-01 17:41:09] [INFO] SERVER READY - About to fork workers
[2025-10-01 17:41:09] [INFO] ============================================================
```

## 4. Forking Worker 1

```
[2025-10-01 17:41:09] [INFO] >>> PRE-FORK: About to fork worker #0
[2025-10-01 17:41:09] [INFO] Booting worker with pid: 39431
[2025-10-01 17:41:09] [INFO] <<< POST-FORK: Worker 39431 has been forked!
[2025-10-01 17:41:09] [INFO] Worker 39431: Calling ldclient.get()...
[2025-10-01 17:41:09] [INFO] Worker 39431: Calling client.postfork()...
[2025-10-01 17:41:09] [INFO] ✅ Worker 39431: LaunchDarkly postfork() completed successfully!
```

## 5. Forking Worker 2

```
[2025-10-01 17:41:09] [INFO] >>> PRE-FORK: About to fork worker #1
[2025-10-01 17:41:09] [INFO] Booting worker with pid: 39432
[2025-10-01 17:41:09] [INFO] <<< POST-FORK: Worker 39432 has been forked!
[2025-10-01 17:41:09] [INFO] Worker 39432: Calling ldclient.get()...
[2025-10-01 17:41:09] [INFO] Worker 39432: Calling client.postfork()...
[2025-10-01 17:41:09] [INFO] ✅ Worker 39432: LaunchDarkly postfork() completed successfully!
```

## 6. Access Logs (when you test endpoints)

```
[2025-10-01 17:41:15] [INFO] GET / HTTP/1.1 200 OK
[2025-10-01 17:41:20] [INFO] GET /flag HTTP/1.1 200 OK
```

## The Complete Fork Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Master Process (PID 39430)                        │
│  - Starting gunicorn                                        │
│  - MASTER PROCESS STARTING                                 │
│  - 🚀 Initializing LaunchDarkly (ONLY ONCE)                │
│  - ✅ Client initialized                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ fork() - Creates Worker 1
                          ├──────────────────────────────┐
                          ▼                              │
┌─────────────────────────────────────────┐              │
│  Step 2: PRE-FORK Worker #0             │              │
│  >>> PRE-FORK: About to fork worker #0  │              │
└─────────────────────┬───────────────────┘              │
                      ▼                                  │
┌─────────────────────────────────────────┐              │
│  Step 3: POST-FORK Worker 1 (PID 39431) │              │
│  <<< POST-FORK: Worker 39431 forked     │              │
│  - Calling ldclient.get()               │              │
│  - Calling client.postfork()            │              │
│  - ✅ postfork() completed!             │              │
└─────────────────────────────────────────┘              │
                                                         │
                                                         │
              ┌──────────────────────────────────────────┘
              │ fork() - Creates Worker 2
              ▼
┌─────────────────────────────────────────┐
│  Step 4: PRE-FORK Worker #1             │
│  >>> PRE-FORK: About to fork worker #1  │
└─────────────────────┬───────────────────┘
                      ▼
┌─────────────────────────────────────────┐
│  Step 5: POST-FORK Worker 2 (PID 39432) │
│  <<< POST-FORK: Worker 39432 forked     │
│  - Calling ldclient.get()               │
│  - Calling client.postfork()            │
│  - ✅ postfork() completed!             │
└─────────────────────────────────────────┘
```

## What's Happening?

1. **Master starts** → LaunchDarkly client initialized ONCE
2. **Master forks Worker 1** → Worker inherits LD client
3. **Worker 1 calls postfork()** → Reinitializes threads
4. **Master forks Worker 2** → Worker inherits LD client  
5. **Worker 2 calls postfork()** → Reinitializes threads
6. **All workers ready** → Can handle requests with live flag updates

## To See This Yourself

Run either:
```bash
./start_with_logs.sh
```

Or:
```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py --preload app:app
```

Then in another terminal, test it:
```bash
curl http://localhost:8000/
curl http://localhost:8000/flag
```

You'll see access logs appear showing which worker handled each request! 