"""
Test Change Impact Detection System End-to-End
"""
import requests
import json
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:8001/api"
EMAIL = "admin@tulipmedical.com"
PASSWORD = "password123"

def test_change_impact():
    """Test the complete change impact detection workflow"""
    
    print("=" * 80)
    print("CHANGE IMPACT DETECTION - END-TO-END TEST")
    print("=" * 80)
    
    # Step 1: Login
    print("\n[1/4] Authenticating...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Authenticated as {EMAIL}")
    
    # Step 2: Ingest QSP sections
    print("\n[2/4] Ingesting sample QSP sections...")
    with open('sample_qsp_sections.json', 'r') as f:
        qsp_data = json.load(f)
    
    ingest_response = requests.post(
        f"{BASE_URL}/impact/ingest_qsp",
        json={
            "doc_name": "Tulip Medical QSP Master Document",
            "sections": qsp_data
        },
        headers=headers
    )
    
    if ingest_response.status_code != 200:
        print(f"❌ Ingestion failed: {ingest_response.text}")
        return
    
    ingest_result = ingest_response.json()
    print(f"✅ Ingested {ingest_result['sections_embedded']} QSP sections")
    print(f"   Document ID: {ingest_result['doc_id']}")
    
    # Step 3: Analyze change impacts
    print("\n[3/4] Analyzing ISO 13485:2024 changes...")
    with open('sample_deltas.json', 'r') as f:
        deltas = json.load(f)
    
    analyze_response = requests.post(
        f"{BASE_URL}/impact/analyze",
        json={
            "deltas": deltas,
            "top_k": 3
        },
        headers=headers
    )
    
    if analyze_response.status_code != 200:
        print(f"❌ Analysis failed: {analyze_response.text}")
        return
    
    analysis_result = analyze_response.json()
    run_id = analysis_result['run_id']
    
    print(f"✅ Analysis complete!")
    print(f"   Run ID: {run_id}")
    print(f"   Changes analyzed: {analysis_result['total_changes_analyzed']}")
    print(f"   Impacts found: {analysis_result['total_impacts_found']}")
    print(f"   Confidence threshold: {analysis_result['threshold']}")
    
    # Display top impacts
    print("\n   Top Impacts Detected:")
    print("   " + "-" * 76)
    
    for i, impact in enumerate(analysis_result['impacts'][:10], 1):
        print(f"\n   {i}. Clause {impact['clause_id']} → {impact['qsp_doc']}")
        print(f"      Section: {impact['section_path']} - {impact['heading']}")
        print(f"      Confidence: {impact['confidence']:.1%}")
        print(f"      Type: {impact['change_type']}")
        print(f"      Rationale: {impact['rationale'][:120]}...")
    
    # Step 4: Get report
    print("\n[4/4] Generating report...")
    
    # JSON report
    report_response = requests.get(
        f"{BASE_URL}/impact/report/{run_id}?format=json",
        headers=headers
    )
    
    if report_response.status_code != 200:
        print(f"❌ Report generation failed: {report_response.text}")
        return
    
    report = report_response.json()
    print(f"✅ JSON report generated")
    print(f"   Status: {report['status']}")
    print(f"   Total impacts: {report['total_impacts']}")
    
    # CSV export
    csv_response = requests.get(
        f"{BASE_URL}/impact/report/{run_id}?format=csv",
        headers=headers
    )
    
    if csv_response.status_code == 200:
        with open(f'impact_report_{run_id}.csv', 'w') as f:
            f.write(csv_response.text)
        print(f"✅ CSV report saved: impact_report_{run_id}.csv")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    
    # Calculate statistics
    impacts_by_clause = {}
    for impact in analysis_result['impacts']:
        clause = impact['clause_id']
        if clause not in impacts_by_clause:
            impacts_by_clause[clause] = []
        impacts_by_clause[clause].append(impact)
    
    print(f"\nSummary by Regulatory Change:")
    for clause, impacts in impacts_by_clause.items():
        avg_conf = sum(i['confidence'] for i in impacts) / len(impacts)
        print(f"  • {clause}: {len(impacts)} QSP sections affected (avg confidence: {avg_conf:.1%})")
    
    # Confidence distribution
    high_conf = sum(1 for i in analysis_result['impacts'] if i['confidence'] > 0.75)
    medium_conf = sum(1 for i in analysis_result['impacts'] if 0.60 <= i['confidence'] <= 0.75)
    low_conf = sum(1 for i in analysis_result['impacts'] if i['confidence'] < 0.60)
    
    print(f"\nConfidence Distribution:")
    print(f"  • High (>75%):   {high_conf} impacts")
    print(f"  • Medium (60-75%): {medium_conf} impacts")
    print(f"  • Low (<60%):    {low_conf} impacts")
    
    print("\n✅ Change Impact Detection system is operational!")
    print(f"   Review the CSV report for full details: impact_report_{run_id}.csv\n")


if __name__ == "__main__":
    try:
        test_change_impact()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
