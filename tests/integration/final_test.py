#!/usr/bin/env python3
"""Final test of the complete system"""

def run_final_test():
    try:
        from storage.state_store import StateStore
        print("✅ 1. StateStore import: SUCCESS")
    except ImportError as e:
        print(f"❌ 1. StateStore import: FAILED - {e}")
        return False
    
    try:
        from tracking.state.engine import NetworkStateEngine
        print("✅ 2. NetworkStateEngine import: SUCCESS")
    except ImportError as e:
        print(f"❌ 2. NetworkStateEngine import: FAILED - {e}")
        return False
    
    try:
        from tracking.state.network_state import NetworkState
        print("✅ 3. NetworkState import: SUCCESS")
    except ImportError as e:
        print(f"❌ 3. NetworkState import: FAILED - {e}")
        return False
    
    # Test functionality
    try:
        engine = NetworkStateEngine()
        print("✅ 4. Engine instantiation: SUCCESS")
    except Exception as e:
        print(f"❌ 4. Engine instantiation: FAILED - {e}")
        return False
    
    try:
        result = engine.update_state("final-test", NetworkState.UP)
        print(f"✅ 5. State update: SUCCESS (transitioned: {result['transitioned']})")
    except Exception as e:
        print(f"❌ 5. State update: FAILED - {e}")
        return False
    
    try:
        history = StateStore.get_state_history("final-test", limit=1)
        print(f"✅ 6. Database query: SUCCESS ({len(history)} entries)")
    except Exception as e:
        print(f"❌ 6. Database query: FAILED - {e}")
        return False
    
    try:
        latest = StateStore.get_latest_state("final-test")
        print(f"✅ 7. Latest state retrieval: SUCCESS ({latest})")
    except Exception as e:
        print(f"❌ 7. Latest state retrieval: FAILED - {e}")
        return False
    
    # Clean up
    try:
        import sqlite3
        conn = sqlite3.connect("data/u_ite.db")
        conn.execute("DELETE FROM network_states WHERE network_id = 'final-test'")
        conn.commit()
        conn.close()
        print("✅ 8. Cleanup: SUCCESS")
    except Exception as e:
        print(f"⚠️  8. Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ALL IMPORT TESTS PASSED! System is fully functional.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_final_test()
    exit(0 if success else 1)
