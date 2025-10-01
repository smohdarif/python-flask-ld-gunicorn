import os
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load .env for local/dev (no effect in most prod setups)
load_dotenv()

import ldclient
from ldclient.config import Config as LDConfig
from ldclient import Context

# ---------------------------
# Initialize LaunchDarkly client
# This runs once in the master process when using --preload
# Workers will call postfork() to reinitialize threads
# ---------------------------
SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
if not SDK_KEY:
    raise RuntimeError("Set LAUNCHDARKLY_SDK_KEY (e.g., in .env or the environment).")

# Initialize client once (will be shared with --preload, then postfork() in workers)
ldclient.set_config(LDConfig(SDK_KEY))
client = ldclient.get()

app = Flask(__name__)

@app.route("/flag")
def read_flag():
    """
    Simple endpoint that evaluates a flag for an anonymous 'user'.
    """
    try:
        flag_key = os.getenv("LD_FLAG_KEY", "sample-flag")
        # Create proper Context object (not a dict!)
        context = Context.builder("anon").build()
        
        if client.is_initialized():
            value = client.variation(flag_key, context, default=False)
            return jsonify({"flag": flag_key, "value": value, "initialized": True})
        else:
            return jsonify({"error": "LaunchDarkly client not initialized", "flag": flag_key, "value": False, "initialized": False})
    except Exception as e:
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@app.get("/")
def home():
    return "Flask + LaunchDarkly + Gunicorn OK"
