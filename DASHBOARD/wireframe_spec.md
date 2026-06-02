# CRN Telemetry Dashboard – Wireframe Specification v0.3
**Seed Node:** Taylor's Lakeside Campus, Subang Jaya

## Overview
A real-time, read-only dashboard for the public and node operators to verify the integrity of the CRN network. 
**Core function:** Ingest signed VRFP envelopes → display Merkle root, power/water metrics, and signature verification status.

## UI Layout (Desktop First, Responsive)

### Header
- **Logo/Title:** Coral Regeneration Network – Telemetry
- **Live Timestamp:** UTC / Local
- **Governance Badge:** "Human Protocol Active - SQA Verified"

### Main Panels (3 Columns)

| Left Panel: Node Status | Center Panel: VRFP Audit | Right Panel: Resource Flow |
|-------------------------|--------------------------|----------------------------|
| List of active nodes    | Current Merkle Root      | Live Power Gauge (mW/m²)   |
| Last heartbeat time     | Cryptographic Signature  | Hard red zones: <50, >200  |
| Fault/Brownout alerts   | Verification Status (✅/❌)| Water Yield (Liters/day)   |

### Bottom Section (Collapsible)
- **Raw JSON Envelope Viewer:** Shows the exact payload canonicalized and signed by the node.
- **Event Log:** System messages (node registered, fault injected, envelope verified).

## Technology Stack (Frontend Target)
- HTML5 / Tailwind CSS
- Vanilla JavaScript fetching from FastAPI (`/latest`, `/merkle`)
