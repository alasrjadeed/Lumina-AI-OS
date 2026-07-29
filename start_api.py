#!/usr/bin/env python3
"""Start the Lumina API server persistently."""
import uvicorn, os, sys, signal, atexit

pid_file = "/tmp/lumina_api.pid"

def write_pid():
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

def cleanup():
    if os.path.exists(pid_file):
        os.remove(pid_file)

atexit.register(cleanup)
write_pid()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    log_level="info",
    reload=False,
    workers=1,
)
