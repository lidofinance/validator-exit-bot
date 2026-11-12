import os

# Set required env vars before any test module is imported.
# src/variables.py validates these at import time.
os.environ.setdefault("WEB3_RPC_ENDPOINTS", "http://localhost:8545")
os.environ.setdefault("CONSENSUS_CLIENT_URL", "http://localhost:5052")
