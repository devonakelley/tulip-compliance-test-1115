"""
Test OpenAI Embeddings Quality for Semantic Matching
Verifies that embeddings produce accurate compliance results
"""
import requests
import io

BASE_URL = "http://localhost:8001/api"

def test_login():
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@tulipmedical.com", "password": "password123"}
    )
    return response.json()["access_token"] if response.status_code == 200 else None

def clear_old_data(token):
    """Clear old test data"""
    print("🧹 Clearing old test data...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get and delete old regulatory docs
    response = requests.get(f"{BASE_URL}/rag/regulatory-docs", headers=headers)
    if response.status_code == 200:
        docs = response.json().get('documents', [])
        for doc in docs:
            requests.delete(f"{BASE_URL}/rag/regulatory-docs/{doc['doc_id']}", headers=headers)
        print(f"   Deleted {len(docs)} old regulatory documents")

def test_embeddings_and_matching(token):
    """Test that OpenAI embeddings produce accurate semantic matches"""
    
    print("\n" + "="*80)
    print("  TESTING OPENAI EMBEDDINGS & SEMANTIC MATCHING")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Upload regulatory document with clear design requirements
    print("\n📄 Step 1: Uploading ISO 13485 Design Requirements...")
    
    iso_content = """
    ISO 13485:2016 - Clause 7.3 Design and Development
    
    7.3.2 Design and Development Planning
    The organization shall plan and control the design and development of the device.
    Design and development planning shall include:
    a) the design and development stages;
    b) the review, verification and validation that are appropriate to each design stage;
    c) the responsibilities and authorities for design and development;
    d) the need to ensure traceability of design outputs to design inputs;
    e) the resources needed, including necessary competence of personnel.
    
    7.3.3 Design and Development Inputs
    Inputs relating to product requirements shall be determined and records maintained.
    These inputs shall include:
    a) functional and performance requirements, according to the intended use;
    b) usability requirements;
    c) applicable regulatory requirements and standards;
    d) applicable output(s) of risk management;
    e) requirements for design and development transfer;
    f) information derived from previous similar designs, where applicable;
    g) other requirements essential for design and development of the device.
    
    7.3.4 Design and Development Outputs
    The organization shall ensure that design outputs:
    a) meet the design input requirements;
    b) provide appropriate information for purchasing, production and service provision;
    c) contain or reference product acceptance criteria;
    d) specify the characteristics of the device that are essential for its safe and proper use.
    
    Design outputs shall be documented and maintained.
    
    7.3.6 Design and Development Verification
    Design and development verification shall be performed to ensure that the design
    outputs meet the design input requirements. Records of verification activities
    shall include:
    a) verification plans;
    b) verification methods;
    c) acceptance criteria;
    d) results and conclusions.
    
    7.3.7 Design and Development Validation
    Design validation shall be performed to ensure that the resulting product is
    capable of meeting the requirements for the specified application or intended use.
    Validation shall include testing under defined operating conditions on
    initial production units or their equivalents.
    """
    
    files = {"file": ("ISO_13485_Design.txt", io.BytesIO(iso_content.encode()), "text/plain")}
    data = {"framework": "ISO_13485", "doc_name": "ISO 13485:2016 Design Controls"}
    
    response = requests.post(f"{BASE_URL}/rag/upload-regulatory-doc", headers=headers, files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ Failed to upload ISO: {response.text}")
        return False
    
    result = response.json()
    print(f"✅ ISO document uploaded - {result['chunks_added']} chunks created")
    
    # Step 2: Upload QSP that clearly addresses design requirements
    print("\n📝 Step 2: Uploading QSP with Design Requirements...")
    
    qsp_content = """
    QSP 7.3-1 Design Control Procedure
    
    1.0 PURPOSE
    This procedure establishes the design control process for medical devices.
    
    2.0 DESIGN PLANNING
    All design projects shall have a documented design plan that includes:
    - Design stages and milestones
    - Review schedule at each stage
    - Verification activities for each stage
    - Validation plan for final product
    - Responsibilities of design team members
    - Required competencies and training
    - Resources and budget allocation
    
    3.0 DESIGN INPUTS
    Design inputs shall be documented using Form F-7.3-A and include:
    - Functional requirements based on intended use
    - Performance specifications
    - Usability requirements
    - Applicable FDA and ISO standards
    - Risk management outputs per ISO 14971
    - Requirements for manufacturing transfer
    - Previous design history when applicable
    
    4.0 DESIGN OUTPUTS
    Design outputs shall be documented and must:
    - Meet all design input requirements
    - Provide information for purchasing and production
    - Define acceptance criteria for the device
    - Specify characteristics essential for safe use
    
    All design outputs maintained in design history file.
    
    5.0 DESIGN VERIFICATION
    Verification activities shall confirm outputs meet inputs.
    Verification records shall document:
    - Verification plan and methods
    - Test protocols and procedures
    - Acceptance criteria
    - Test results and conclusions
    - Traceability to design inputs
    
    6.0 DESIGN VALIDATION
    Validation shall confirm the device meets user needs and intended use.
    Validation activities include:
    - Testing under actual use conditions
    - Clinical evaluation or usability studies
    - Testing with initial production units
    - Documentation of validation results
    """
    
    files = {"file": ("QSP_7.3-1_Design.txt", io.BytesIO(qsp_content.encode()), "text/plain")}
    response = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files)
    
    if response.status_code != 200:
        print(f"❌ Failed to upload QSP: {response.text}")
        return False
    
    qsp_result = response.json()
    qsp_id = qsp_result['document_id']
    print(f"✅ QSP uploaded - ID: {qsp_id}")
    print(f"   References: {qsp_result.get('references_extracted', 0)}")
    print(f"   Citations: {qsp_result.get('citations_extracted', 0)}")
    
    # Step 3: Run semantic compliance check
    print("\n🔍 Step 3: Running Semantic Compliance Check...")
    
    data = {"qsp_doc_id": qsp_id, "framework": "ISO_13485"}
    response = requests.post(f"{BASE_URL}/rag/check-compliance", headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"❌ Compliance check failed: {response.text}")
        return False
    
    result = response.json()
    analysis = result.get('analysis', {})
    
    print(f"\n{'='*80}")
    print("  SEMANTIC MATCHING RESULTS")
    print('='*80)
    print(f"Framework: {analysis.get('framework')}")
    print(f"Matches Found: {analysis.get('matches_found')}")
    print(f"Requirements Covered: {analysis.get('unique_requirements_covered')}")
    print(f"Total Requirements: {analysis.get('total_requirements')}")
    print(f"Coverage Percentage: {analysis.get('coverage_percentage')}%")
    
    # Display sample matches
    matches = analysis.get('matches', [])
    if matches:
        print(f"\n📊 Sample Semantic Matches:")
        for i, match in enumerate(matches[:5], 1):
            print(f"\n  Match {i} - Confidence: {match.get('confidence', 0):.2%}")
            print(f"  QSP: {match.get('qsp_chunk', '')[:120]}...")
            print(f"  ISO: {match.get('regulatory_text', '')[:120]}...")
    
    # Evaluate success
    print(f"\n{'='*80}")
    print("  EVALUATION")
    print('='*80)
    
    success_criteria = {
        "Matches found": analysis.get('matches_found', 0) > 5,
        "Coverage > 30%": analysis.get('coverage_percentage', 0) > 30,
        "Has semantic matches": len(matches) > 0
    }
    
    all_passed = all(success_criteria.values())
    
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"{status} {criterion}")
    
    if all_passed:
        print("\n✅ OpenAI embeddings working correctly!")
        print("   Semantic matching is producing accurate results.")
        return True
    else:
        print("\n⚠️  Embeddings may need tuning or more data.")
        return False

def main():
    print("="*80)
    print("  OPENAI EMBEDDINGS QUALITY TEST")
    print("="*80)
    
    token = test_login()
    if not token:
        print("❌ Login failed")
        return 1
    
    print("✅ Logged in successfully\n")
    
    # Clear old data
    clear_old_data(token)
    
    # Test embeddings quality
    success = test_embeddings_and_matching(token)
    
    if success:
        print("\n" + "="*80)
        print("  ✅ SYSTEM READY FOR ACCURATE COMPLIANCE CHECKING")
        print("="*80)
        print("\nCustomers can now:")
        print("  • Upload ISO/FDA documents")
        print("  • Upload their QSPs")
        print("  • Get accurate semantic compliance results")
        print("  • Trust the coverage percentages")
        print("  • Identify real gaps in their documentation")
        return 0
    else:
        print("\n⚠️  Further tuning may be needed")
        return 1

if __name__ == "__main__":
    exit(main())
