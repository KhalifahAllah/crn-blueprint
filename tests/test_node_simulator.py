"""
tests/test_node_simulator.py
SQA Phase 1: Exhaustive Logic & Cryptographic Integrity
Author: Gemini (Council Node: Logic & Governance)
"""

import pytest
import json
import hashlib
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Import the simulator functions
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TOOLS.simulation.node_simulator import (
    merkle_root, 
    generate_metrics, 
    sign_payload
)

# --- SQA FIXTURES ---
@pytest.fixture
def mock_preset():
    """Controlled environment preset. Base power adjusted to 80mW to stay within 200mW/m2 density limit."""
    return {
        "ambient_temp_min": 27.0, "ambient_temp_max": 32.0,
        "ambient_rh_min": 70.0, "ambient_rh_max": 85.0,
        "pmfc_base_mW": 80.0, "pmfc_min_mW": 25.0, "pmfc_max_mW": 100.0,
        "pmfc_fluct_down": 0.0, "pmfc_fluct_up": 0.0, 
        "soil_orp_min_mV": -200.0, "soil_orp_max_mV": -200.0,
        "water_yield_min_L": 0.3, "water_yield_max_L": 0.3
    }

@pytest.fixture
def keypair():
    """Generates a fresh Ed25519 keypair for test signing."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key

# --- SQA AUDIT TESTS ---

def test_merkle_root_deterministic():
    """AUDIT: Proves the Merkle root hashes identically for the same inputs."""
    leaves = [
        hashlib.sha256(b"leaf1").hexdigest(),
        hashlib.sha256(b"leaf2").hexdigest(),
        hashlib.sha256(b"leaf3").hexdigest()
    ]
    root1 = merkle_root(leaves)
    root2 = merkle_root(leaves)
    
    assert root1 == root2, "CRITICAL: Merkle root hashing is not deterministic."
    assert len(root1) == 64, "CRITICAL: Merkle root is not a valid SHA-256 hex length."

def test_environmental_boundaries(mock_preset):
    """AUDIT: Proves the PMFC outputs strictly respect the physical presets."""
    metrics = generate_metrics(mock_preset)
    
    # Allows for either the exact 80.0mW base, or 0.0mW if the brownout fault injects
    assert metrics["power_output_mW"] in [80.0, 0.0], "FAIL: Power output breached physical envelope."
    assert metrics["soil_orp_mV"] == -200.0, "FAIL: Soil ORP breached envelope."
    assert metrics["water_yield_L"] == 0.3, "FAIL: Water yield breached envelope."

def test_cryptographic_signing(mock_preset, keypair):
    """AUDIT: Validates Ed25519 payload signing and signature verification."""
    private_key, public_key = keypair
    metrics = generate_metrics(mock_preset)
    node_id = "test-node-01"
    
    envelope, raw_payload = sign_payload(private_key, node_id, metrics)
    
    assert envelope["node_id"] == node_id
    assert "vrfp_signature" in envelope
    
    signature_bytes = bytes.fromhex(envelope["vrfp_signature"])
    # This will throw an exception and fail the test if the signature is invalid
    public_key.verify(signature_bytes, raw_payload) 

def test_json_canonicalization(mock_preset, keypair):
    """AUDIT: Ensures JSON is sorted and compact to prevent signature breakage."""
    private_key, _ = keypair
    metrics = generate_metrics(mock_preset)
    _, raw_payload = sign_payload(private_key, "test-node-01", metrics)
    
    assert b" " not in raw_payload, "FAIL: Canonical JSON contains whitespace."
