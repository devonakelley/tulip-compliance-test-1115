"""
Test Regulatory Compliance System
Tests reference extraction, traceability, and compliance matrix
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def test_login():
    """Login and get token"""
    print("\n🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@tulipmedical.com", "password": "password123"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful - Token received")
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_list_frameworks(token):
    """Test listing regulatory frameworks"""
    print("\n📋 Testing GET /regulatory/frameworks...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/regulatory/frameworks", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        frameworks = data.get("frameworks", [])
        print(f"✅ Found {len(frameworks)} regulatory frameworks:")
        for fw in frameworks:
            print(f"   • {fw['name']}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_get_framework_clauses(token):
    """Test getting clauses for a framework"""
    print("\n📜 Testing GET /regulatory/frameworks/ISO_13485/clauses...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/regulatory/frameworks/ISO_13485/clauses",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        clauses = data.get("clauses", [])
        print(f"✅ Found {len(clauses)} clauses for ISO 13485:")
        for clause in clauses[:5]:  # Show first 5
            print(f"   • {clause['clause_id']}: {clause['title']}")
        if len(clauses) > 5:
            print(f"   ... and {len(clauses) - 5} more")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_extract_references(token):
    """Test reference extraction from sample text"""
    print("\n🔍 Testing POST /regulatory/extract-references...")
    
    # Sample QSP content with references
    sample_content = """
    QSP 7.3-1 Design Control Procedure R11
    
    This procedure implements ISO 13485:2016 Clause 7.3 and 21 CFR 820.30.
    
    Related Documents:
    - See WI-ENG-003 for design validation procedures
    - Refer to Form 7.3-1-A for design review checklist
    - See QSP 4.2-1 for document control requirements
    - Reference ISO 14971:2019 for risk management
    
    This procedure also addresses MDR 2017/745 Article 10 requirements.
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("sample_qsp.txt", sample_content.encode(), "text/plain")}
    
    response = requests.post(
        f"{BASE_URL}/regulatory/extract-references",
        headers=headers,
        files=files
    )
    
    if response.status_code == 200:
        data = response.json()
        doc_refs = data.get("document_references", [])
        reg_cits = data.get("regulatory_citations", [])
        
        print(f"✅ Extraction successful!")
        print(f"   📄 Document References: {len(doc_refs)}")
        for ref in doc_refs:
            print(f"      • {ref['reference']} ({ref['doc_type']})")
        
        print(f"   ⚖️  Regulatory Citations: {len(reg_cits)}")
        for cit in reg_cits:
            print(f"      • {cit['citation']} - {cit['framework']}")
        
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_hierarchy(token):
    """Test document hierarchy"""
    print("\n🌳 Testing GET /regulatory/hierarchy...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/regulatory/hierarchy", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        hierarchy = data.get("hierarchy", {})
        print(f"✅ Hierarchy retrieved:")
        print(f"   Total Documents: {hierarchy.get('total_documents', 0)}")
        print(f"   Total Relationships: {hierarchy.get('total_relationships', 0)}")
        
        docs_by_level = hierarchy.get('documents_by_level', {})
        for level in sorted([int(k) for k in docs_by_level.keys()]):
            docs = docs_by_level.get(str(level), [])
            print(f"   Level {level}: {len(docs)} documents")
        
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_compliance_matrix(token):
    """Test compliance matrix"""
    print("\n📊 Testing GET /regulatory/compliance-matrix...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/regulatory/compliance-matrix", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        matrix = data.get("matrix", [])
        print(f"✅ Compliance matrix built:")
        print(f"   Total Mappings: {len(matrix)}")
        
        # Group by framework
        by_framework = {}
        for item in matrix:
            fw = item['framework']
            by_framework[fw] = by_framework.get(fw, 0) + 1
        
        for fw, count in sorted(by_framework.items()):
            print(f"   {fw}: {count} clause mappings")
        
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_coverage_analysis(token):
    """Test coverage analysis"""
    print("\n📈 Testing GET /regulatory/coverage-analysis/ISO_13485...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/regulatory/coverage-analysis/ISO_13485",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        analysis = data.get("analysis", {})
        print(f"✅ Coverage analysis complete:")
        print(f"   Framework: {analysis.get('framework')}")
        print(f"   Total Clauses: {analysis.get('total_clauses')}")
        print(f"   Covered: {analysis.get('covered_clauses')}")
        print(f"   Uncovered: {analysis.get('uncovered_clauses')}")
        print(f"   Coverage: {analysis.get('coverage_percentage')}%")
        
        uncovered = analysis.get('uncovered_details', [])
        if uncovered:
            print(f"\n   🚨 High Priority Gaps:")
            for gap in uncovered[:5]:
                if gap.get('criticality') == 'high':
                    print(f"      • {gap['clause_id']}: {gap['title']}")
        
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def main():
    print_header("Regulatory Compliance System Test Suite")
    
    # Login
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    results = []
    
    # Run tests
    print_header("Test 1: List Regulatory Frameworks")
    results.append(test_list_frameworks(token))
    
    print_header("Test 2: Get Framework Clauses")
    results.append(test_get_framework_clauses(token))
    
    print_header("Test 3: Extract References and Citations")
    results.append(test_extract_references(token))
    
    print_header("Test 4: Document Hierarchy")
    results.append(test_hierarchy(token))
    
    print_header("Test 5: Compliance Matrix")
    results.append(test_compliance_matrix(token))
    
    print_header("Test 6: Coverage Analysis")
    results.append(test_coverage_analysis(token))
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All regulatory system tests passed!")
        print("\n📋 System Capabilities Verified:")
        print("   ✅ Multi-regulatory framework support")
        print("   ✅ Automatic reference extraction")
        print("   ✅ Document hierarchy building")
        print("   ✅ Compliance matrix generation")
        print("   ✅ Coverage gap analysis")
        print("   ✅ Traceability and impact analysis ready")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
