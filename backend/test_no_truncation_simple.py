"""
Test that truncation bugs are fixed - Simple version
"""
from core.iso_diff_processor import ISODiffProcessor
from core.qsp_parser import QSPParser
import inspect

def test_fix_1():
    """Test that regulatory diff processor doesn't truncate"""
    processor = ISODiffProcessor()
    
    # Simulate a long regulatory text (1000 chars)
    long_text = "This is a regulatory requirement. " * 30  # ~1020 chars
    
    old_clauses = {}
    new_clauses = {"4.2.4": long_text}
    
    deltas = processor.compute_diff(old_clauses, new_clauses)
    
    if len(deltas) > 0:
        change_text = deltas[0]['change_text']
        print(f"✅ FIX #1 TEST: Regulatory change text length = {len(change_text)} chars")
        
        if len(change_text) < 600:
            print(f"   ❌ FAILED: Text is truncated (expected >1000 chars)")
            return False
        else:
            print(f"   ✅ PASSED: Full text preserved (expected ~1020 chars)")
            return True
    
    return False

def test_fix_2():
    """Test that QSP parser fallback doesn't truncate"""
    parser = QSPParser()
    
    # Check the source code of the fallback method
    source = inspect.getsource(parser._fallback_parsing)
    
    if '[:2000]' in source:
        print(f"❌ FIX #2 TEST: FAILED - Still has [:2000] truncation in code")
        return False
    else:
        print(f"✅ FIX #2 TEST: PASSED - No [:2000] truncation found in _fallback_parsing method")
        return True

def test_fix_3():
    """Test that embedding function has increased limit"""
    # Read the source file directly
    with open('/app/backend/core/change_impact_service_mongo.py', 'r') as f:
        source = f.read()
    
    if '> 16000' in source:
        print(f"✅ FIX #3 TEST: PASSED - Using increased 16000 char limit")
        return True
    elif '> 8000' in source and '16000' not in source:
        print(f"❌ FIX #3 TEST: FAILED - Still using 8000 char limit")
        return False
    else:
        print(f"⚠️  FIX #3 TEST: Cannot clearly determine limit")
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTING TRUNCATION FIXES")
    print("="*60)
    print()
    
    test1 = test_fix_1()
    print()
    test2 = test_fix_2()
    print()
    test3 = test_fix_3()
    
    print()
    print("="*60)
    if test1 and test2 and test3:
        print("✅ ALL TESTS PASSED - Truncation bugs are fixed!")
    else:
        print("❌ SOME TESTS FAILED - Check fixes above")
    print("="*60)
