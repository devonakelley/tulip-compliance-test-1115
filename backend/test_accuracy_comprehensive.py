"""
Comprehensive Accuracy Test for Certaro Compliance System
Tests the complete pipeline: diff extraction -> QSP parsing -> gap detection
"""
import asyncio
import json
import os
from core.change_impact_service_mongo import ChangeImpactServiceMongo

async def test_complete_pipeline():
    """
    Test the complete compliance gap detection pipeline
    """
    
    print("="*80)
    print("CERTARO COMPLIANCE SYSTEM - COMPREHENSIVE ACCURACY TEST")
    print("="*80)
    
    # Initialize service
    service = ChangeImpactServiceMongo()
    
    # Load test data
    print("\n📥 Loading test data...")
    try:
        with open('sample_deltas.json', 'r') as f:
            regulatory_changes = json.load(f)
        print(f"   ✅ Loaded {len(regulatory_changes)} regulatory changes")
        
        with open('sample_qsp_sections.json', 'r') as f:
            qsp_sections = json.load(f)
        print(f"   ✅ Loaded {len(qsp_sections)} QSP sections")
        
    except FileNotFoundError as e:
        print(f"   ❌ ERROR: Test data files not found: {e}")
        return
    
    # Verify no truncation in loaded data
    print("\n🔍 Verifying data integrity (no truncation)...")
    
    for idx, change in enumerate(regulatory_changes, 1):
        change_text_len = len(change.get('change_text', ''))
        print(f"   Regulatory change {idx}: {change_text_len} characters")
        
        if change_text_len < 100:
            print(f"      ⚠️  WARNING: Suspiciously short (possible truncation)")
        elif change_text_len > 300:
            print(f"      ✅ Good length (truncation bug is fixed)")
    
    for idx, section in enumerate(qsp_sections, 1):
        section_text_len = len(section.get('text', ''))
        print(f"   QSP section {idx}: {section_text_len} characters")
        
        if section_text_len < 100:
            print(f"      ⚠️  WARNING: Suspiciously short")
    
    # Ingest QSP sections
    print("\n📥 Ingesting QSP sections into system...")
    tenant_id = "accuracy-test"
    
    try:
        ingest_result = service.ingest_qsp_document(
            tenant_id=tenant_id,
            doc_id="test-accuracy-001",
            doc_name="Accuracy Test QSP Set",
            sections=qsp_sections
        )
        print(f"   ✅ Ingested {ingest_result['sections_processed']} QSP sections")
        print(f"   ✅ Generated {ingest_result['embeddings_created']} embeddings")
        
    except Exception as e:
        print(f"   ❌ ERROR during ingestion: {e}")
        return
    
    # Run gap detection analysis
    print("\n🔍 Running gap detection analysis...")
    print("   (This tests the complete AI matching pipeline)")
    
    try:
        analysis_result = await service.detect_impacts_async(
            tenant_id=tenant_id,
            deltas=regulatory_changes,
            top_k=5
        )
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   Total changes analyzed: {analysis_result['total_changes_analyzed']}")
        print(f"   Total impacts found: {analysis_result['total_impacts_found']}")
        print(f"   Confidence threshold: {analysis_result['threshold']}")
        
    except Exception as e:
        print(f"   ❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Analyze results in detail
    print(f"\n{'='*80}")
    print("DETAILED MATCH ANALYSIS")
    print("="*80)
    
    expected_matches = {
        "4.2.4": ["4.2.4", "4.2-4"],  # Electronic records should match
        "7.5.1.1": ["7.5.1", "7.5-1"],  # Process validation should match
        "8.2.6": ["8.2.2", "8.2-2"]  # Post-market surveillance should match
    }
    
    matches_found = {
        "4.2.4": [],
        "7.5.1.1": [],
        "8.2.6": []
    }
    
    critical_matches = 0
    total_expected = 3
    
    for impact in analysis_result['impacts']:
        clause_id = impact['clause_id']
        qsp_doc = impact['qsp_doc']
        confidence = impact['confidence_score']
        rationale = impact.get('rationale', 'No rationale provided')
        
        print(f"\n🔸 Regulatory Change: {clause_id}")
        print(f"   → Matched QSP: {qsp_doc}")
        print(f"   → Confidence: {confidence:.1%}")
        print(f"   → Rationale: {rationale[:150]}...")
        
        # Check if this is an expected critical match
        if clause_id in expected_matches:
            for expected_qsp in expected_matches[clause_id]:
                if expected_qsp in qsp_doc:
                    matches_found[clause_id].append(qsp_doc)
                    print(f"   ✅ CRITICAL MATCH VERIFIED")
                    break
    
    # Count critical matches found
    for clause_id, found_qsps in matches_found.items():
        if found_qsps:
            critical_matches += 1
    
    # Check for false positives
    print(f"\n{'='*80}")
    print("FALSE POSITIVE CHECK")
    print("="*80)
    
    false_positives = 0
    
    for impact in analysis_result['impacts']:
        clause_id = impact['clause_id']
        qsp_doc = impact['qsp_doc']
        confidence = impact['confidence_score']
        
        # Check for obviously wrong matches
        # E.g., electronic records (4.2.4) shouldn't match complaints (8.2.1)
        if clause_id == "4.2.4" and "8.2" in qsp_doc and "8.2.4" not in qsp_doc:
            print(f"⚠️  Potential false positive: {clause_id} → {qsp_doc} ({confidence:.1%})")
            if confidence > 0.65:
                false_positives += 1
                print(f"   ❌ HIGH CONFIDENCE FALSE POSITIVE")
        
        # Validation (7.5.1.1) shouldn't match complaints or infrastructure
        if clause_id == "7.5.1.1" and ("8.2.1" in qsp_doc or "6.3" in qsp_doc):
            print(f"⚠️  Potential false positive: {clause_id} → {qsp_doc} ({confidence:.1%})")
            if confidence > 0.65:
                false_positives += 1
                print(f"   ❌ HIGH CONFIDENCE FALSE POSITIVE")
    
    if false_positives == 0:
        print("✅ No high-confidence false positives detected")
    
    # Calculate accuracy metrics
    print(f"\n{'='*80}")
    print("ACCURACY METRICS")
    print("="*80)
    
    print(f"\n📊 Critical Match Detection:")
    print(f"   Expected matches: {total_expected}")
    print(f"   Matches found: {critical_matches}")
    print(f"   Success rate: {critical_matches/total_expected*100:.1f}%")
    
    if critical_matches == total_expected:
        print(f"   ✅ ALL CRITICAL MATCHES FOUND")
    elif critical_matches >= 2:
        print(f"   ⚠️  PARTIAL SUCCESS - Some matches found")
    else:
        print(f"   ❌ FAILED - Missing critical matches")
    
    print(f"\n📊 False Positive Rate:")
    print(f"   High-confidence false positives: {false_positives}")
    
    if false_positives == 0:
        print(f"   ✅ EXCELLENT - No false alarms")
    elif false_positives <= 2:
        print(f"   ⚠️  ACCEPTABLE - Few false alarms")
    else:
        print(f"   ❌ POOR - Too many false alarms")
    
    # Overall verdict
    print(f"\n{'='*80}")
    print("OVERALL SYSTEM VERDICT")
    print("="*80)
    
    if critical_matches == total_expected and false_positives == 0:
        print("✅ EXCELLENT - System is highly accurate")
        print("   • All critical gaps detected")
        print("   • No false positives")
        print("   • Ready for production deployment")
        verdict = "PRODUCTION_READY"
    
    elif critical_matches >= 2 and false_positives <= 1:
        print("🟡 GOOD - System is acceptably accurate")
        print("   • Most critical gaps detected")
        print("   • Minimal false positives")
        print("   • Ready for deployment with human oversight")
        verdict = "ACCEPTABLE_WITH_OVERSIGHT"
    
    else:
        print("❌ NEEDS IMPROVEMENT - Accuracy issues detected")
        print("   • Missing critical matches or too many false positives")
        print("   • Not ready for production deployment")
        print("   • Requires investigation and tuning")
        verdict = "NOT_READY"
    
    print("="*80)
    
    # Save results
    test_results = {
        "verdict": verdict,
        "critical_matches": critical_matches,
        "total_expected": total_expected,
        "false_positives": false_positives,
        "total_impacts_found": analysis_result['total_impacts_found'],
        "matches_detail": matches_found
    }
    
    with open('accuracy_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: accuracy_test_results.json")
    
    return test_results

if __name__ == "__main__":
    result = asyncio.run(test_complete_pipeline())
    
    # Exit with appropriate code
    if result and result['verdict'] == "PRODUCTION_READY":
        exit(0)  # Success
    elif result and result['verdict'] == "ACCEPTABLE_WITH_OVERSIGHT":
        exit(0)  # Acceptable
    else:
        exit(1)  # Not ready
