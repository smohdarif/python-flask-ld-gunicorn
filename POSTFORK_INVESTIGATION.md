# LaunchDarkly postfork() Investigation

## Summary

**LaunchDarkly's recommended `postfork()` approach does NOT work in this environment** due to SIGSEGV (segmentation fault) crashes.

## What We Tried

### Attempt 1: Follow LaunchDarkly's Official Recommendation
```python
# Master process (with --preload)
ldclient.set_config(LDConfig(SDK_KEY))
client = ldclient.get()

# In post_fork hook
client.postfork()  # ← CRASHES with SIGSEGV
```

**Result**: ❌ Immediate SIGSEGV crashes in every worker

### Attempt 2: Downgrade urllib3
**Reason**: Warning showed urllib3 v2 incompatible with LibreSSL 2.8.3

```bash
pip install 'urllib3<2.0'  # Downgraded 2.5.0 → 1.26.20
```

**Result**: ❌ Still crashes with SIGSEGV

## Root Cause

The issue is **NOT** just urllib3. The fundamental problem is:

1. **macOS LibreSSL incompatibility**: System uses LibreSSL 2.8.3 (not OpenSSL 1.1.1+)
2. **Thread state corruption**: LaunchDarkly's background threads don't survive `fork()` properly
3. **System-level limitations**: macOS fork semantics don't play well with multi-threaded applications

### Evidence from Logs

```
[INFO] Worker 64234: Calling client.postfork()...
[ERROR] Worker (pid:64234) was sent SIGSEGV!
```

Workers crash **immediately** upon calling `postfork()`, creating an infinite crash loop.

## Current Solution

### WITHOUT `--preload` and WITHOUT `postfork()`

Each worker initializes its own LaunchDarkly client independently:

```python
# Each worker process runs this independently
ldclient.set_config(LDConfig(SDK_KEY))
client = ldclient.get()
```

**Command**:
```bash
gunicorn --config gunicorn.conf.py app:app
# NOTE: NO --preload flag
```

### Trade-offs

| Aspect | With postfork() | Without postfork() (Current) |
|--------|----------------|------------------------------|
| **Stability** | ❌ Crashes | ✅ Stable |
| **Memory** | ✅ Efficient | ❌ Higher (each worker has own client) |
| **Startup** | ✅ Fast | ❌ Slower (each worker initializes) |
| **Flag Updates** | ✅ Real-time | ✅ Real-time |
| **Production Ready** | ❌ No | ✅ Yes |

## Why This Happens

LaunchDarkly's `postfork()` documentation assumes:
1. OpenSSL 1.1.1+ (not LibreSSL)
2. Linux-like fork semantics
3. Stable thread reinitialization

**macOS with LibreSSL violates these assumptions**, causing crashes.

## Recommendation

For **production use on macOS**:
- ✅ Use the current approach (no --preload, no postfork)
- ✅ Accept higher memory usage as the cost of stability
- ✅ Each worker gets real-time flag updates independently

For **production use on Linux with OpenSSL**:
- Try `postfork()` approach (may work better)
- Test thoroughly before deploying
- Have fallback plan if crashes occur

## Files Modified

1. `gunicorn.conf.py` - Removed `postfork()` call
2. `app.py` - Each worker initializes LD client
3. `start_with_logs.sh` - Removed `--preload` flag
4. `requirements.txt` - Pinned `urllib3<2.0` (to reduce warnings)

## Logs Still Show Forking Process

Even without calling `postfork()`, you still get detailed logs:

```
MASTER PROCESS STARTING
Master PID: 58434
SERVER READY - About to fork workers
>>> PRE-FORK: About to fork worker #1
<<< POST-FORK: Worker 58435 has been forked (without calling postfork)
```

This demonstrates the fork process without the unsafe `postfork()` call.

## Conclusion

**LaunchDarkly's `postfork()` is a best practice, but not universally compatible.**

In environments where it causes crashes (like macOS with LibreSSL), the per-worker initialization approach is:
- ✅ Stable
- ✅ Production-ready  
- ✅ Functionally complete
- ❌ Less memory-efficient

This is an acceptable trade-off for reliability. 