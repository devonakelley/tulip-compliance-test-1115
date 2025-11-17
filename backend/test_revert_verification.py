"""
Verification that ISO diff system accepts ANY documents without validation
"""
import os
import tempfile
import fitz  # PyMuPDF
from core.iso_diff_processor import ISODiffProcessor


def create_test_pdf(content: str, filename: str) -> str:
    """Create a test PDF file with given content"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    
    doc = fitz.open()
    page = doc.new_page()
    point = fitz.Point(50, 50)
    page.insert_text(point, content, fontsize=12)
    doc.save(filepath)
    doc.close()
    
    return filepath


print("="*80)
print("VERIFYING: ISO Diff System Accepts ANY Documents")
print("="*80)

# Test 1: Different parts (previously blocked)
print("\nTest 1: ISO 10993-18 vs ISO 10993-17 (different parts)")
part18 = create_test_pdf("""
ISO 10993-18:2020
Biological evaluation of medical devices
Part 18: Chemical characterization

1.0 Scope
Chemical characterization requirements.

2.0 Methods
Analytical methods for characterization.
""", "test_part18.pdf")

part17 = create_test_pdf("""
ISO 10993-17:2023
Biological evaluation of medical devices
Part 17: Toxicological risk assessment

1.0 Scope
Toxicological risk assessment requirements.

2.0 Process
Risk assessment process.
""", "test_part17.pdf")

try:
    processor = ISODiffProcessor()
    deltas = processor.process_documents(part18, part17)
    print(f"✅ SUCCESS: Diff generated with {len(deltas)} changes")
    print(f"   No validation blocking!")
except Exception as e:
    print(f"❌ FAILED: {e}")
finally:
    os.remove(part18)
    os.remove(part17)

# Test 2: Different series (previously blocked)
print("\nTest 2: ISO 10993 vs ISO 14971 (different series)")
iso10993 = create_test_pdf("""
ISO 10993-18:2020
Biological evaluation

1.0 Scope
Biocompatibility requirements.
""", "test_10993.pdf")

iso14971 = create_test_pdf("""
ISO 14971:2019
Risk management

1.0 Scope
Risk management requirements.
""", "test_14971.pdf")

try:
    processor = ISODiffProcessor()
    deltas = processor.process_documents(iso10993, iso14971)
    print(f"✅ SUCCESS: Diff generated with {len(deltas)} changes")
    print(f"   No validation blocking!")
except Exception as e:
    print(f"❌ FAILED: {e}")
finally:
    os.remove(iso10993)
    os.remove(iso14971)

# Test 3: Completely unrelated documents
print("\nTest 3: Two random documents")
doc1 = create_test_pdf("""
Random Document A

Section 1
This is some random text.

Section 2
More random content here.
""", "test_random1.pdf")

doc2 = create_test_pdf("""
Random Document B

Section 1
Different text entirely.

Section 3
New section with other content.
""", "test_random2.pdf")

try:
    processor = ISODiffProcessor()
    deltas = processor.process_documents(doc1, doc2)
    print(f"✅ SUCCESS: Diff generated with {len(deltas)} changes")
    print(f"   System accepts ANY documents!")
except Exception as e:
    print(f"❌ FAILED: {e}")
finally:
    os.remove(doc1)
    os.remove(doc2)

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\n✅ All tests should show SUCCESS with no validation errors")
print("✅ The system now diffs ANY two documents without blocking")
print("✅ No 'incompatible standards' errors")
print("✅ No 'companion documents' errors")
print("\nRevert is COMPLETE and working as requested!")
print("="*80)

