#!/usr/bin/env python3
"""Test full history storage"""

import time
import sqlite3
from tracking.state.engine import NetworkStateEngine
from tracking.state.network_state import NetworkState
from storage.state_store import StateStore

def test_full_history():
    print("Testing Full History Storage")
    print("=" * 60)
    
    engine = NetworkStateEngine()
    network_id = "full-history-test"
    
    # Clear any existing test data
    db_path = "data/u_ite.db"
    conn = sqlite3.connect(db_path)
    conn.execute(f"DELETE FROM network_states WHERE network_id = ?", (network_id,))
    conn.commit()
    conn.close()
    
    # Simulate a network lifecycle
    print("1. Network comes UP")
    engine.update_state(network_id, NetworkState.UP)
    time.sleep(0.5)
    
    print("2. Network goes DEGRADED")
    engine.update_state(network_id, NetworkState.DEGRADED)
    time.sleep(1)
    
    print("3. Network goes DOWN")
    engine.update_state(network_id, NetworkState.DOWN)
    time.sleep(2)
    
    print("4. Network recovers (UP)")
    result = engine.update_state(network_id, NetworkState.UP)
    downtime = result['downtime_seconds']
    print(f"   Downtime: {downtime} seconds")
    
    print("5. Network goes DEGRADED again")
    engine.update_state(network_id, NetworkState.DEGRADED)
    
    # Check history
    print("\n" + "=" * 60)
    print("Database History:")
    print("=" * 60)
    
    history = StateStore.get_state_history(network_id)
    print(f"Total entries: {len(history)}")
    
    for i, entry in enumerate(history, 1):
        downtime_str = f"{entry['downtime_seconds']}s" if entry['downtime_seconds'] else "N/A"
        print(f"{i:2}. ID:{entry['id']:3} | State: {entry['state']:10} | Downtime: {downtime_str:6} | Time: {entry['timestamp'][11:19]}")
    
    # Verify we have multiple entries for same network
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT COUNT(DISTINCT state) as unique_states FROM network_states WHERE network_id = ?",
        (network_id,)
    )
    unique_states = cursor.fetchone()[0]
    conn.close()
    
    print(f"\nUnique states stored: {unique_states} (should be 3: UP, DEGRADED, DOWN)")
    print("✓ Full history is working!" if len(history) == 5 else "✗ History not working properly")
    
    return len(history) == 5

if __name__ == "__main__":
    if test_full_history():
        print("\n✅ All tests passed! Full history storage is working.")
    else:
        print("\n❌ Tests failed!")
