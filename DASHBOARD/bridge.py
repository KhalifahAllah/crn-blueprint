# DASHBOARD/bridge.py
import time
import requests
import json
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

NODE_ID = "sj-taylors-alpha-01"
API_URL = "http://127.0.0.1:8000"

print("--- CRN Telemetry Bridge (Claude API Edition) ---")
print("Generating session keys...")
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()
pub_hex = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
).hex()

print(f"Registering Node with API: {pub_hex[:16]}...")
reg_payload = {"node_id": NODE_ID, "public_key_hex": pub_hex}
res = requests.post(f"{API_URL}/nodes/register", json=reg_payload)
print(f"API Response: {res.json()}")

print("\nStarting Live Telemetry Feed (Press CTRL+C to stop)...")

try:
    while True:
        # Create metrics matching Claude's strict Pydantic model
        metrics = {
            "power_density_mw_per_m2": 85.5,
            "module_power_mw": 42.75,
            "soil_orp_mv": -210.0,
            "water_yield_l": 0.15,
            "ambient_rh_pct": 78.0,
            "ambient_temp_c": 29.5,
            "biome": "equatorial_tropical",
            "data_status": "MODELED_EXPECTATION"
        }
        
        # Canonicalize and sign
        canonical = json.dumps(metrics, sort_keys=True, separators=(',', ':')).encode()
        sig = private_key.sign(canonical).hex()
        
        envelope = {
            "node_id": NODE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "vrfp_signature": sig
        }
        
        # Send to API
        ingest_res = requests.post(f"{API_URL}/telemetry/ingest", json=envelope)
        
        if ingest_res.status_code == 200:
            print(f"[SUCCESS] Sent Payload -> API Status: {ingest_res.json()['status']} | Total Stored: {ingest_res.json()['payload_count']}")
        else:
            print(f"[ERROR] API Error: {ingest_res.text}")
            
        time.sleep(2)
except KeyboardInterrupt:
    print("\nFeed stopped.")
