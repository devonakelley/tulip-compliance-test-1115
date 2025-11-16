"""
Integration test for ISO Diff System with Standard Identification
Tests the complete workflow from PDF input to delta output
"""
import os
import tempfile
import fitz  # PyMuPDF
from core.iso_diff_processor import ISODiffProcessor


def create_test_pdf(content: str, filename: str) -> str:
    """Create a test PDF file with given content"""
    # Create temporary directory if it doesn't exist
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    # Create PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # Add text to page
    point = fitz.Point(50, 50)
    page.insert_text(point, content, fontsize=12)
    
    # Save
    doc.save(filepath)
    doc.close()
    
    return filepath


def test_version_diff():
    """Test VERSION_DIFF mode - same part, different years"""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST 1: Version Diff (Same Part, Different Years)")
    print("="*80)
    
    # Create test PDFs with same part, different years
    old_content = """
ISO 10993-18:2005
Biological evaluation of medical devices
Part 18: Chemical characterization of materials

1.0 Scope
This standard specifies requirements for chemical characterization.

2.0 General Requirements
Organizations shall establish procedures for chemical analysis.

3.0 Test Methods
Standard test methods shall be used.
"""
    
    new_content = """
ISO 10993-18:2020
Biological evaluation of medical devices
Part 18: Chemical characterization of medical device materials

1.0 Scope
This standard specifies comprehensive requirements for chemical characterization.

2.0 General Requirements
Organizations shall establish and maintain procedures for chemical analysis.

3.0 Test Methods
Validated test methods shall be used according to ISO 17025.

4.0 Reporting
Results shall be documented in accordance with regulatory requirements.
"""
    
    old_pdf = create_test_pdf(old_content, "test_iso_10993_18_2005.pdf")
    new_pdf = create_test_pdf(new_content, "test_iso_10993_18_2020.pdf")
    
    try:
        processor = ISODiffProcessor()
        
        # This should work - same part, different years
        result = processor.analyze_documents(old_pdf, new_pdf)
        
        assert result['analysis_type'] == 'VERSION_DIFF', f"Expected VERSION_DIFF, got {result['analysis_type']}"
        assert result['old_standard'] == 'ISO 10993-18:2005', f"Old standard mismatch: {result['old_standard']}"
        assert result['new_standard'] == 'ISO 10993-18:2020', f"New standard mismatch: {result['new_standard']}"
        assert len(result['deltas']) > 0, "Should have detected changes"
        
        print(f"✅ Test PASSED: Version diff completed successfully")
        print(f"   Old: {result['old_standard']}")
        print(f"   New: {result['new_standard']}")
        print(f"   Changes detected: {result['total_changes']}")
        
        # Check change types
        added = sum(1 for d in result['deltas'] if d['change_type'] == 'added')
        modified = sum(1 for d in result['deltas'] if d['change_type'] == 'modified')
        print(f"   Added clauses: {added}")
        print(f"   Modified clauses: {modified}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(old_pdf):
            os.remove(old_pdf)
        if os.path.exists(new_pdf):
            os.remove(new_pdf)


def test_cross_reference():
    """Test CROSS_REFERENCE mode - different parts, same series"""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST 2: Cross-Reference (Different Parts, Same Series)")
    print("="*80)
    
    # Create test PDFs with different parts (THIS IS THE KEY TEST)
    part18_content = """
ISO 10993-18:2020
Biological evaluation of medical devices
Part 18: Chemical characterization of medical device materials

1.0 Scope
This part specifies requirements for chemical characterization.

2.0 Analytical Methods
Standard analytical methods shall be used for characterization.
"""
    
    part17_content = """
ISO 10993-17:2023
Biological evaluation of medical devices
Part 17: Establishment of allowable limits for leachable substances

1.0 Scope
This part specifies requirements for toxicological risk assessment.

2.0 Risk Assessment
Toxicological risk assessment shall be performed for all leachables.
"""
    
    part18_pdf = create_test_pdf(part18_content, "test_iso_10993_18_2020.pdf")
    part17_pdf = create_test_pdf(part17_content, "test_iso_10993_17_2023.pdf")
    
    try:
        processor = ISODiffProcessor()
        
        # This should return CROSS_REFERENCE, not perform a diff
        result = processor.analyze_documents(part18_pdf, part17_pdf)
        
        assert result['analysis_type'] == 'CROSS_REFERENCE', f"Expected CROSS_REFERENCE, got {result['analysis_type']}"
        assert 'companion documents' in result['message'].lower(), "Should mention companion documents"
        assert len(result['next_steps']) > 0, "Should provide next steps"
        
        print(f"✅ Test PASSED: Cross-reference detected correctly")
        print(f"   Message: {result['message']}")
        print(f"   Recommendation: {result['recommendation']}")
        print(f"   Next steps:")
        for step in result['next_steps']:
            print(f"     - {step}")
        
        print(f"\n   🎯 KEY ACHIEVEMENT: System correctly identified that Part 18 and Part 17")
        print(f"      are different parts and should NOT be diffed against each other!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(part18_pdf):
            os.remove(part18_pdf)
        if os.path.exists(part17_pdf):
            os.remove(part17_pdf)


def test_incompatible_series():
    """Test INCOMPATIBLE mode - different series"""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST 3: Incompatible Documents (Different Series)")
    print("="*80)
    
    # Create test PDFs with different series
    iso10993_content = """
ISO 10993-18:2020
Biological evaluation of medical devices
Part 18: Chemical characterization
"""
    
    iso14971_content = """
ISO 14971-1:2019
Medical devices - Application of risk management
Part 1: General requirements
"""
    
    iso10993_pdf = create_test_pdf(iso10993_content, "test_iso_10993.pdf")
    iso14971_pdf = create_test_pdf(iso14971_content, "test_iso_14971.pdf")
    
    try:
        processor = ISODiffProcessor()
        
        # This should raise ValueError for incompatible documents
        try:
            result = processor.analyze_documents(iso10993_pdf, iso14971_pdf)
            print(f"❌ Test FAILED: Should have raised ValueError for incompatible documents")
            return False
        except ValueError as ve:
            error_msg = str(ve)
            assert 'Cannot compare' in error_msg or 'Different standard series' in error_msg, f"Unexpected error message: {error_msg}"
            
            print(f"✅ Test PASSED: Correctly rejected incompatible documents")
            print(f"   Error message: {error_msg[:200]}...")
            return True
        
    except Exception as e:
        print(f"❌ Test FAILED with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(iso10993_pdf):
            os.remove(iso10993_pdf)
        if os.path.exists(iso14971_pdf):
            os.remove(iso14971_pdf)


def test_process_documents_wrapper():
    """Test process_documents method with standard identification"""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST 4: process_documents() Wrapper Method")
    print("="*80)
    
    # Create test PDFs
    old_content = """
ISO 10993-5:2009
Biological evaluation of medical devices
Part 5: Tests for in vitro cytotoxicity

1.0 Scope
This standard specifies test methods for cytotoxicity.
"""
    
    new_content = """
ISO 10993-5:2020
Biological evaluation of medical devices
Part 5: Tests for in vitro cytotoxicity

1.0 Scope
This standard specifies enhanced test methods for cytotoxicity evaluation.

2.0 New Requirements
Additional requirements for test validation.
"""
    
    old_pdf = create_test_pdf(old_content, "test_part5_old.pdf")
    new_pdf = create_test_pdf(new_content, "test_part5_new.pdf")
    
    try:
        processor = ISODiffProcessor()
        
        # Test the process_documents method (used by API)
        deltas = processor.process_documents(old_pdf, new_pdf)
        
        assert isinstance(deltas, list), "Should return list of deltas"
        assert len(deltas) > 0, "Should detect changes"
        
        print(f"✅ Test PASSED: process_documents() working correctly")
        print(f"   Deltas returned: {len(deltas)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(old_pdf):
            os.remove(old_pdf)
        if os.path.exists(new_pdf):
            os.remove(new_pdf)


def run_all_integration_tests():
    """Run all integration tests"""
    
    print("\n" + "="*80)
    print("RUNNING ISO DIFF INTEGRATION TESTS")
    print("="*80)
    
    results = {
        "Version Diff": test_version_diff(),
        "Cross-Reference Detection": test_cross_reference(),
        "Incompatible Series": test_incompatible_series(),
        "process_documents Wrapper": test_process_documents_wrapper()
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "="*80)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*80)
        print("\n🎯 KEY ACHIEVEMENT:")
        print("   The system now correctly prevents diffing of different ISO parts.")
        print("   ISO 10993-18 and ISO 10993-17 are identified as companion standards,")
        print("   not as versions to be diffed.")
        print("\n✅ The fix is complete and working!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ SOME TESTS FAILED - See details above")
        print("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)
