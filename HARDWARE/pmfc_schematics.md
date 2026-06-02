# PMFC Module Schematic & Assembly – CRN v0.1 Alpha

## 1. Physical Topology
The CRN Alpha module utilizes a standard 0.5m² HDPE tray acting as the physical boundary. 
- **Anode:** Carbon felt buried in the anaerobic rhizosphere (soil/sediment).
- **Cathode:** 316L Stainless steel mesh resting above the soil line, exposed to oxygen.
- **Edge Compute:** Housed in an IP67 waterproof junction box mounted above the water line.

## 2. Power Envelope & Harvesting
PMFCs generate low-voltage, continuous milliwatt power (target: 50-200 mW/m²). The ESP32 requires burst currents of ~250mA to transmit WiFi. Therefore, a direct drive is impossible.
- Raw PMFC leads connect to a **BQ25504 Energy Harvester**.
- The harvester trickles charge into a **LiFePO4 buffer battery**.
- The ESP32 remains in Deep Sleep (consuming <20µA), waking only every 15 minutes to sample, sign, and transmit.

## 3. Data Wiring (ESP32-WROOM-32D)
- **I2C Bus (GPIO 21 SDA / GPIO 22 SCL):** 
  - ATECC608A Secure Element (Address 0x60)
  - SHT40 Temp/RH Sensor (Address 0x44)
  - INA219 Power Monitor (Address 0x40)
- **Analog In (GPIO 34):** Soil ORP Probe (via differential amplifier)

## 4. Cryptographic Flow
1. ESP32 wakes and polls sensors.
2. ESP32 constructs canonical JSON payload.
3. ESP32 sends payload hash to ATECC608A via I2C.
4. ATECC608A signs hash using permanently locked private key.
5. ESP32 transmits signed envelope to FastAPI backend and returns to sleep.
