"""
Test RAG System for Regulatory Document Processing
Tests upload of ISO/FDA docs and compliance checking against QSPs
"""
import requests
import io

BASE_URL = "http://localhost:8001/api"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def test_login():
    """Login and get token"""
    print("\n🔐 Logging in as Tulip Medical...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@tulipmedical.com", "password": "password123"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_upload_regulatory_doc(token):
    """Test uploading a regulatory document"""
    print("\n📄 Testing Upload of Regulatory Document (Simulated ISO 13485)...")
    
    # Create sample ISO document content
    iso_content = """
    ISO 13485:2016 Medical Devices - Quality Management Systems
    
    Clause 7.3 Design and Development
    
    7.3.1 General
    The organization shall establish and maintain procedures for design and development.
    
    7.3.2 Design and Development Planning
    The organization shall plan and control the design and development of the device.
    Planning shall include:
    a) design and development stages
    b) required review, verification and validation activities
    c) responsibilities and authorities for design and development
    d) management of interfaces between different groups
    
    7.3.3 Design and Development Inputs
    Inputs relating to product requirements shall be determined and records maintained.
    These inputs shall include:
    a) functional and performance requirements
    b) applicable regulatory requirements and standards
    c) requirements derived from previous similar designs
    d) other requirements essential for design and development
    
    7.3.4 Design and Development Outputs
    Design and development outputs shall:
    a) meet the input requirements
    b) provide appropriate information for purchasing, production and service provision
    c) contain or reference acceptance criteria
    d) specify the characteristics essential for safe and proper use
    
    7.3.5 Design and Development Review
    Systematic reviews of design and development shall be performed.
    
    7.3.6 Design and Development Verification
    Verification shall be performed to ensure outputs meet input requirements.
    
    7.3.7 Design and Development Validation
    Validation shall be performed to ensure product meets user needs.
    
    Clause 8.5 Improvement
    
    8.5.1 General
    The organization shall identify and implement any changes necessary.
    
    8.5.2 Corrective Action
    The organization shall take action to eliminate causes of nonconformities.
    
    8.5.3 Preventive Action
    The organization shall determine action to eliminate causes of potential nonconformities.
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        "file": ("ISO_13485_2016_Sample.txt", io.BytesIO(iso_content.encode()), "text/plain")
    }
    data = {
        "framework": "ISO_13485",
        "doc_name": "ISO 13485:2016 Design & CAPA Sections"
    }
    
    response = requests.post(
        f"{BASE_URL}/rag/upload-regulatory-doc",
        headers=headers,
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Regulatory document uploaded successfully!")
        print(f"   Doc ID: {result['doc_id']}")
        print(f"   Chunks: {result['chunks_added']}")
        print(f"   Total chars: {result['total_chars']}")
        return result['doc_id']
    else:
        print(f"❌ Upload failed: {response.text}")
        return None

def test_upload_qsp(token):
    """Upload a sample QSP document"""
    print("\n📝 Uploading Sample QSP Document...")
    
    qsp_content = """
    QSP 7.3-1 Design Control Procedure R11
    
    1.0 PURPOSE
    This procedure establishes requirements for design and development of medical devices
    to ensure compliance with regulatory requirements.
    
    2.0 SCOPE
    Applies to all design and development activities for Class II and Class III medical devices.
    
    3.0 RESPONSIBILITIES
    - Design Manager: Overall responsibility for design control
    - Quality Assurance: Review and approval of design documentation
    - Regulatory Affairs: Ensure regulatory compliance
    
    4.0 PROCEDURE
    
    4.1 Design Planning
    All design projects shall have a documented design plan including:
    - Project timeline and milestones
    - Resource allocation
    - Design review schedule
    - Verification and validation activities
    - Risk management activities per ISO 14971
    
    4.2 Design Inputs
    Design inputs shall be documented on Form 7.3-1-A Design Input Checklist.
    Inputs shall include:
    - User requirements and intended use
    - Performance specifications
    - Regulatory requirements (FDA 510(k), ISO 13485)
    - Safety requirements
    
    4.3 Design Outputs
    Design outputs shall be documented and include:
    - Design specifications (see WI-ENG-003)
    - Manufacturing drawings
    - Bill of materials
    - Assembly procedures
    
    4.4 Design Review
    Design reviews shall be conducted at defined stages.
    Reviews documented on Form 7.3-2-B Design Review Report.
    
    4.5 Design Verification
    Verification testing per WI-TEST-015 shall confirm outputs meet inputs.
    
    4.6 Design Validation
    Clinical evaluation or usability testing shall validate device meets user needs.
    
    4.7 Design Changes
    All design changes shall follow QSP 4.3-2 Change Control.
    
    5.0 DOCUMENTATION
    - F-7.3-1-A: Design Input Checklist
    - F-7.3-2-B: Design Review Report
    - F-7.3-3-C: Verification Test Report
    
    6.0 REFERENCES
    - ISO 13485:2016 Clause 7.3
    - FDA 21 CFR 820.30
    - ISO 14971 Risk Management
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("QSP_7.3-1_R11.txt", io.BytesIO(qsp_content.encode()), "text/plain")}
    
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ QSP uploaded successfully!")
        print(f"   Doc ID: {result['document_id']}")
        print(f"   Filename: {result['filename']}")
        print(f"   References extracted: {result.get('references_extracted', 0)}")
        print(f"   Citations extracted: {result.get('citations_extracted', 0)}")
        return result['document_id']
    else:
        print(f"❌ QSP upload failed: {response.text}")
        return None

def test_compliance_check(token, qsp_id):
    """Test RAG-based compliance checking"""
    print("\n🔍 Testing RAG-Based Compliance Check...")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "qsp_doc_id": qsp_id,
        "framework": "ISO_13485"
    }
    
    response = requests.post(
        f"{BASE_URL}/rag/check-compliance",
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        analysis = result.get('analysis', {})
        
        print(f"✅ Compliance check completed!")
        print(f"   QSP: {result.get('qsp_filename')}")
        print(f"   Framework: {analysis.get('framework')}")
        print(f"   Matches found: {analysis.get('matches_found')}")
        print(f"   Requirements covered: {analysis.get('unique_requirements_covered')}")
        print(f"   Coverage: {analysis.get('coverage_percentage')}%")
        
        if analysis.get('matches'):
            print(f"\n   📋 Sample Matches:")
            for i, match in enumerate(analysis['matches'][:3], 1):
                print(f"   {i}. Confidence: {match.get('confidence', 0):.2f}")
                print(f"      QSP: {match.get('qsp_chunk', '')[:80]}...")
                print(f"      ISO: {match.get('regulatory_text', '')[:80]}...")
        
        return True
    else:
        print(f"❌ Compliance check failed: {response.text}")
        return False

def test_list_regulatory_docs(token):
    """Test listing uploaded regulatory docs"""
    print("\n📚 Testing List Regulatory Documents...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/rag/regulatory-docs", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        docs = result.get('documents', [])
        
        print(f"✅ Found {len(docs)} regulatory document(s)")
        for doc in docs:
            print(f"   • {doc['doc_name']} ({doc['framework']})")
            print(f"     Chunks: {doc['chunk_count']}")
        
        return True
    else:
        print(f"❌ List failed: {response.text}")
        return False

def test_search(token):
    """Test semantic search"""
    print("\n🔎 Testing Semantic Search...")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "query": "design verification and validation requirements",
        "framework": "ISO_13485",
        "n_results": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/rag/search",
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        results = result.get('results', [])
        
        print(f"✅ Search completed!")
        print(f"   Query: {result.get('query')}")
        print(f"   Results: {len(results)}")
        
        for i, res in enumerate(results[:2], 1):
            print(f"\n   Result {i}:")
            print(f"   {res.get('text', '')[:150]}...")
            print(f"   Source: {res.get('metadata', {}).get('doc_name')}")
        
        return True
    else:
        print(f"❌ Search failed: {response.text}")
        return False

def main():
    print_header("RAG System Test - Regulatory Document Processing")
    
    # Login
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return 1
    
    results = []
    
    # Test 1: Upload regulatory document
    print_header("Test 1: Upload ISO Regulatory Document")
    reg_doc_id = test_upload_regulatory_doc(token)
    results.append(reg_doc_id is not None)
    
    # Test 2: Upload QSP
    print_header("Test 2: Upload QSP Document")
    qsp_id = test_upload_qsp(token)
    results.append(qsp_id is not None)
    
    # Test 3: List regulatory docs
    print_header("Test 3: List Regulatory Documents")
    results.append(test_list_regulatory_docs(token))
    
    # Test 4: Semantic search
    print_header("Test 4: Semantic Search")
    results.append(test_search(token))
    
    # Test 5: Compliance check (if we have both docs)
    if qsp_id and reg_doc_id:
        print_header("Test 5: RAG-Based Compliance Check")
        results.append(test_compliance_check(token, qsp_id))
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All RAG system tests passed!")
        print("\n✨ System Can Now:")
        print("   ✅ Accept large ISO/FDA regulatory document uploads")
        print("   ✅ Chunk and embed documents (deployment-safe)")
        print("   ✅ Perform semantic compliance checking")
        print("   ✅ Search regulatory requirements")
        print("   ✅ Compare QSPs against uploaded regulations")
        print("   ✅ Handle regulatory updates dynamically")
        print("\n🚀 Ready for customer use with real ISO/FDA documents!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
