#!/usr/bin/env python3
"""Test the correct imports"""

# Method 1: Import separately (RECOMMENDED)
from tracking.state.engine import NetworkStateEngine
from tracking.state.network_state import NetworkState

print("Testing separate imports...")
engine = NetworkStateEngine()

result1 = engine.update_state("net-001", NetworkState.DOWN)
print(f"DOWN transition: {result1['transitioned']}")

result2 = engine.update_state("net-001", NetworkState.UP)
print(f"UP transition: {result2['transitioned']}")

# Check if downtime was calculated
if result2['downtime_seconds']:
    print(f"Downtime: {result2['downtime_seconds']} seconds")
