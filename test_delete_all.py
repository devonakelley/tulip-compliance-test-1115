#!/usr/bin/env python3

import sys
from backend_test import QSPComplianceAPITester

def main():
    """Run delete all endpoints test"""
    tester = QSPComplianceAPITester()
    
    print("🔍 TESTING DELETE ALL ENDPOINTS")
    print("=" * 60)
    
    success = tester.run_delete_all_endpoints_test()
    
    if success:
        print("\n✅ Delete All Endpoints Test PASSED")
        return 0
    else:
        print("\n❌ Delete All Endpoints Test FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())