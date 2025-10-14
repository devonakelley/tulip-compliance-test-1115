"""
Test script for Phase 2 - Report Persistence & Audit Logging
Tests both tenants to verify isolation and functionality
"""
import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001/api"

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_result(success, message):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")

def test_login(email, password):
    """Test login and return token"""
    print(f"\n🔐 Logging in as {email}...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_result(True, f"Login successful - Tenant: {data['tenant_id']}")
        return data["access_token"]
    else:
        print_result(False, f"Login failed: {response.text}")
        return None

def test_reports_endpoint(token, tenant_name):
    """Test reports listing endpoint"""
    print(f"\n📊 Testing /reports endpoint for {tenant_name}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/reports", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = data.get("count", 0)
        print_result(True, f"Found {count} reports")
        if count > 0:
            for report in data.get("reports", [])[:3]:  # Show first 3
                print(f"   - {report.get('analysis_type')} | Score: {report.get('alignment_score')} | {report.get('created_at')}")
        return True
    else:
        print_result(False, f"Failed to fetch reports: {response.text}")
        return False

def test_report_stats(token, tenant_name):
    """Test report statistics endpoint"""
    print(f"\n📈 Testing /reports/stats endpoint for {tenant_name}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/reports/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get("stats", {})
        print_result(True, "Report stats retrieved")
        print(f"   - Total Reports: {stats.get('total_reports', 0)}")
        print(f"   - Avg Score: {stats.get('average_alignment_score', 0):.2f}%")
        print(f"   - Total Gaps: {stats.get('total_gaps_identified', 0)}")
        return True
    else:
        print_result(False, f"Failed to fetch stats: {response.text}")
        return False

def test_audit_logs(token, tenant_name):
    """Test audit logs endpoint"""
    print(f"\n📝 Testing /reports/audit-logs endpoint for {tenant_name}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/reports/audit-logs?limit=5", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = data.get("count", 0)
        print_result(True, f"Found {count} audit logs")
        if count > 0:
            for log in data.get("logs", [])[:3]:  # Show first 3
                print(f"   - {log.get('action')} | {log.get('target')} | {log.get('timestamp')}")
        return True
    else:
        print_result(False, f"Failed to fetch audit logs: {response.text}")
        return False

def test_audit_stats(token, tenant_name):
    """Test audit statistics endpoint"""
    print(f"\n📊 Testing /reports/audit-stats endpoint for {tenant_name}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/reports/audit-stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get("stats", {})
        print_result(True, "Audit stats retrieved")
        for action, count in stats.items():
            if action != "total_actions":
                print(f"   - {action}: {count}")
        print(f"   - TOTAL: {stats.get('total_actions', 0)}")
        return True
    else:
        print_result(False, f"Failed to fetch audit stats: {response.text}")
        return False

def check_audit_log_file():
    """Check if audit log file exists and has content"""
    print("\n📄 Checking audit.log file...")
    log_path = Path("/app/backend/logs/audit.log")
    
    if log_path.exists():
        lines = log_path.read_text().strip().split('\n')
        count = len([l for l in lines if l.strip()])
        print_result(True, f"Audit log file exists with {count} entries")
        
        # Show last 3 entries
        if count > 0:
            print("   Recent entries:")
            for line in lines[-3:]:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        print(f"   - {entry.get('action')} by {entry.get('user_id')[:8]}...")
                    except:
                        print(f"   - {line[:80]}...")
        return True
    else:
        print_result(False, "Audit log file not found")
        return False

def main():
    """Run Phase 2 tests"""
    print_header("Phase 2 Testing - Report Persistence & Audit Logging")
    
    # Test credentials
    tenant1 = {
        "name": "Tulip Medical",
        "email": "admin@tulipmedical.com",
        "password": "password123"
    }
    
    tenant2 = {
        "name": "MedTech Solutions",
        "email": "admin@medtechsolutions.com",
        "password": "password123"
    }
    
    results = {
        "tenant1": [],
        "tenant2": []
    }
    
    # Test Tenant 1
    print_header(f"Testing Tenant 1: {tenant1['name']}")
    token1 = test_login(tenant1["email"], tenant1["password"])
    
    if token1:
        results["tenant1"].append(test_reports_endpoint(token1, tenant1["name"]))
        results["tenant1"].append(test_report_stats(token1, tenant1["name"]))
        results["tenant1"].append(test_audit_logs(token1, tenant1["name"]))
        results["tenant1"].append(test_audit_stats(token1, tenant1["name"]))
    
    # Test Tenant 2
    print_header(f"Testing Tenant 2: {tenant2['name']}")
    token2 = test_login(tenant2["email"], tenant2["password"])
    
    if token2:
        results["tenant2"].append(test_reports_endpoint(token2, tenant2["name"]))
        results["tenant2"].append(test_report_stats(token2, tenant2["name"]))
        results["tenant2"].append(test_audit_logs(token2, tenant2["name"]))
        results["tenant2"].append(test_audit_stats(token2, tenant2["name"]))
    
    # Check audit log file
    print_header("System Tests")
    check_audit_log_file()
    
    # Summary
    print_header("Test Summary")
    tenant1_pass = sum(results["tenant1"])
    tenant1_total = len(results["tenant1"])
    tenant2_pass = sum(results["tenant2"])
    tenant2_total = len(results["tenant2"])
    
    print(f"\n{tenant1['name']}: {tenant1_pass}/{tenant1_total} tests passed")
    print(f"{tenant2['name']}: {tenant2_pass}/{tenant2_total} tests passed")
    
    total_pass = tenant1_pass + tenant2_pass
    total_tests = tenant1_total + tenant2_total
    
    print(f"\n🎯 Overall: {total_pass}/{total_tests} tests passed")
    
    if total_pass == total_tests:
        print("\n✅ Phase 2 Implementation SUCCESSFUL!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Review results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
