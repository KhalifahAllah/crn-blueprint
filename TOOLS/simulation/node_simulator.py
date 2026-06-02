#!/usr/bin/env python3
"""
TOOLS/simulation/node_simulator.py

Enhanced CRN Node Simulator:
- CLI config for biome presets
- Emits signed telemetry envelopes (using modern 'cryptography' library)
- Writes per-sample output and daily snapshot with Merkle root
- Configurable output paths and cadence

AI-assisted synthesis: Council (Copilot / MetaAIness / Gemini)
"""

import argparse
import json
import os
import random
from datetime import datetime, timezone
import hashlib
import pathlib
import sys

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("Missing dependency: pip install cryptography", file=sys.stderr)
    sys.exit(1)

NODE_ID_DEFAULT = "sj-taylors-alpha-01"

# --- Utility: Merkle root for list of bytes ---
def merkle_root(hex_leaves):
    if not hex_leaves:
        return ""
    nodes = [bytes.fromhex(h) for h in hex_leaves]
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        new_nodes = []
        for i in range(0, len(nodes), 2):
            new_nodes.append(hashlib.sha256(nodes[i] + nodes[i+1]).digest())
        nodes = new_nodes
    return nodes[0].hex()

# --- Telemetry generation bounded by preset ---
def generate_metrics(preset):
    ambient_temp = round(random.uniform(preset["ambient_temp_min"], preset["ambient_temp_max"]), 1)
    ambient_rh = round(random.uniform(preset["ambient_rh_min"], preset["ambient_rh_max"]), 1)

    base_power = preset["pmfc_base_mW"]
    power_fluctuation = random.uniform(-preset["pmfc_fluct_down"], preset["pmfc_fluct_up"])
    
    # Fault Injection: 5% chance of brownout
    if random.random() < 0.05:
        current_power_mW = 0.0
    else:
        current_power_mW = round(max(preset["pmfc_min_mW"], min(preset["pmfc_max_mW"], base_power + power_fluctuation)), 2)

    soil_orp_mV = round(random.uniform(preset["soil_orp_min_mV"], preset["soil_orp_max_mV"]), 1)
    water_yield_L = round(random.uniform(preset["water_yield_min_L"], preset["water_yield_max_L"]), 3)

    return {
        "power_output_mW": current_power_mW,
        "soil_orp_mV": soil_orp_mV,
        "water_yield_L": water_yield_L,
        "ambient_rh_percent": ambient_rh,
        "ambient_temp_c": ambient_temp
    }

# --- Signing and envelope creation ---
def sign_payload(private_key, node_id, metrics):
    payload_string = json.dumps(metrics, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = private_key.sign(payload_string)
    envelope = {
        "node_id": node_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "vrfp_signature": signature.hex()
    }
    return envelope, payload_string

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)

# --- CLI and main flow ---
def load_preset(path):
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="CRN Node Simulator (enhanced)")
    parser.add_argument("--config", type=str, default="TOOLS/simulation/presets/equatorial.yaml", help="Preset YAML path")
    parser.add_argument("--output", type=str, default="sim_payload.json", help="Single envelope output path")
    parser.add_argument("--snapshot-dir", type=str, default="DASHBOARD/snapshots", help="Directory for daily snapshots")
    parser.add_argument("--count", type=int, default=6, help="Number of samples to generate")
    parser.add_argument("--node-id", type=str, default=NODE_ID_DEFAULT, help="Node identifier")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if not os.path.exists(args.config):
        print(f"Error: Config file not found at {args.config}")
        sys.exit(1)

    preset = load_preset(args.config)

    # Generate modern Ed25519 keypair using 'cryptography'
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_hex = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ).hex()

    envelopes = []
    leaf_hashes = []
    for i in range(args.count):
        metrics = generate_metrics(preset)
        env, raw = sign_payload(private_key, args.node_id, metrics)
        envelopes.append(env)
        leaf_hashes.append(hashlib.sha256(raw).hexdigest())

    root = merkle_root(leaf_hashes)

    # Snapshot structure
    snapshot = {
        "node_id": args.node_id,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "envelopes": envelopes,
        "merkle_root": root,
        "verifying_key_hex": pub_hex
    }

    # Write output files
    pathlib.Path(args.snapshot_dir).mkdir(parents=True, exist_ok=True)
    snapshot_path = os.path.join(args.snapshot_dir, f"v0.1-alpha-sim-{snapshot['date']}.json")
    write_json(snapshot_path, snapshot)
    write_json(args.output, envelopes[-1])

    print(f"\n--- Simulation Complete ---")
    print(f"Node ID: {args.node_id}")
    print(f"Snapshot written to: {snapshot_path}")
    print(f"Latest payload written to: {args.output}")
    print(f"Public Key (Hex): {pub_hex}")
    print(f"Merkle Root: {root}\n")

if __name__ == "__main__":
    main()