#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class QSPComplianceAPITester:
    def __init__(self, base_url="https://iso13485-tool.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Database: {data.get('database', 'N/A')}, AI: {data.get('ai_service', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Health Check", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("API Root Endpoint", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_database_connectivity(self):
        """Test database connectivity endpoint"""
        try:
            response = requests.get(f"{self.api_url}/test/database", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"MongoDB Status: {data.get('status', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Database Connectivity", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("Database Connectivity", False, f"Exception: {str(e)}")
            return False

    def test_ai_service(self):
        """Test AI service functionality"""
        try:
            response = requests.get(f"{self.api_url}/test/ai", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"AI Response: {data.get('response', 'N/A')[:100]}..."
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("AI Service", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("AI Service", False, f"Exception: {str(e)}")
            return False

    def test_document_upload_simple(self):
        """Test simple document upload endpoint"""
        try:
            test_content = "This is a test QSP document for compliance checking."
            params = {
                'filename': 'test_document.txt',
                'content': test_content
            }
            response = requests.post(f"{self.api_url}/test/upload", params=params, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Upload Status: {data.get('status', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Simple Document Upload", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("Simple Document Upload", False, f"Exception: {str(e)}")
            return False

    def test_list_test_documents(self):
        """Test list documents endpoint"""
        try:
            response = requests.get(f"{self.api_url}/test/documents", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Documents Found: {len(data) if isinstance(data, list) else 'N/A'}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("List Test Documents", success, details, response.json() if success else response.text)
            return success
            
        except Exception as e:
            self.log_test("List Test Documents", False, f"Exception: {str(e)}")
            return False

    def test_dashboard_endpoint(self):
        """Test dashboard data endpoint"""
        try:
            response = requests.get(f"{self.api_url}/dashboard", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Compliance Score: {data.get('compliance_score', 0)}%, Documents: {data.get('total_documents', 0)}, Gaps: {data.get('gaps_count', 0)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Dashboard Data", success, details, response.json() if success else response.text)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Dashboard Data", False, f"Exception: {str(e)}")
            return False, {}

    def create_test_qsp_file(self):
        """Create a test QSP document file"""
        content = """Quality System Procedure - Document Control

1. PURPOSE
This procedure establishes the requirements for document control within the quality management system.

2. SCOPE
This procedure applies to all controlled documents used in the quality management system.

3. RESPONSIBILITIES
3.1 Quality Manager
- Approve all quality system documents
- Ensure document control procedures are followed

3.2 Document Control Coordinator
- Maintain master list of controlled documents
- Distribute controlled documents
- Collect and destroy obsolete documents

4. PROCEDURE
4.1 Document Creation
All quality system documents shall be created using approved templates.

4.2 Document Review and Approval
Documents shall be reviewed for adequacy and approved prior to issue.

4.3 Document Distribution
Controlled documents shall be distributed to designated locations.

4.4 Document Changes
Changes to documents shall be reviewed and approved by the same functions that performed the original review.

5. RECORDS
Records of document control activities shall be maintained.
"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def create_test_iso_summary(self):
        """Create a test ISO 13485:2024 summary file"""
        content = """ISO 13485:2024 Summary of Changes

NEW CLAUSES:
4.1.6 Outsourced processes - Enhanced requirements for control of outsourced processes
7.3.10 Design transfer - New requirements for design transfer activities
8.2.6 Post-market surveillance - Enhanced post-market surveillance requirements

MODIFIED CLAUSES:
4.2.4 Control of documents - Updated requirements for electronic document control
5.5.2 Management representative - Modified responsibilities for management representative
7.1 Planning of product realization - Enhanced planning requirements
7.5.1 Control of production and service provision - Updated production control requirements
8.5.2 Corrective action - Enhanced corrective action requirements

The 2024 revision introduces significant changes to risk management integration,
software lifecycle processes, and cybersecurity considerations for medical devices.
"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def test_qsp_document_upload(self):
        """Test QSP document upload"""
        test_file = None
        try:
            test_file = self.create_test_qsp_file()
            
            with open(test_file, 'rb') as f:
                files = {'file': ('test_qsp_document.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/documents/upload", files=files, timeout=30)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Document ID: {data.get('document_id', 'N/A')}, Sections: {data.get('sections_count', 0)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("QSP Document Upload", success, details, response.json() if success else response.text)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("QSP Document Upload", False, f"Exception: {str(e)}")
            return False, {}
        finally:
            if test_file and os.path.exists(test_file):
                os.unlink(test_file)

    def test_iso_summary_upload(self):
        """Test ISO summary upload"""
        test_file = None
        try:
            test_file = self.create_test_iso_summary()
            
            with open(test_file, 'rb') as f:
                files = {'file': ('iso_13485_2024_summary.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/iso-summary/upload", files=files, timeout=30)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Summary ID: {data.get('summary_id', 'N/A')}, New Clauses: {data.get('new_clauses_count', 0)}, Modified: {data.get('modified_clauses_count', 0)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("ISO Summary Upload", success, details, response.json() if success else response.text)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("ISO Summary Upload", False, f"Exception: {str(e)}")
            return False, {}
        finally:
            if test_file and os.path.exists(test_file):
                os.unlink(test_file)

    def test_invalid_file_upload(self):
        """Test invalid file upload handling"""
        try:
            # Create a fake PDF file (not supported)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False)
            temp_file.write("This is not a real PDF")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('invalid_file.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/documents/upload", files=files, timeout=10)
            
            # Should fail with 400 status
            success = response.status_code == 400
            details = f"Status: {response.status_code} (Expected 400 for invalid file type)"
            
            self.log_test("Invalid File Upload Handling", success, details, response.text)
            
            os.unlink(temp_file.name)
            return success
            
        except Exception as e:
            self.log_test("Invalid File Upload Handling", False, f"Exception: {str(e)}")
            return False

    def test_clause_mapping_analysis(self):
        """Test AI clause mapping analysis"""
        try:
            response = requests.post(f"{self.api_url}/analysis/run-mapping", timeout=60)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Documents Processed: {data.get('total_documents_processed', 0)}, Mappings Generated: {data.get('total_mappings_generated', 0)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("AI Clause Mapping Analysis", success, details, response.json() if success else response.text)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("AI Clause Mapping Analysis", False, f"Exception: {str(e)}")
            return False, {}

    def test_compliance_gap_analysis(self):
        """Test compliance gap analysis"""
        try:
            response = requests.post(f"{self.api_url}/analysis/run-compliance", timeout=60)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Overall Score: {data.get('overall_score', 0)}%, Gaps Found: {data.get('gaps_found', 0)}, Affected Docs: {data.get('affected_documents', 0)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Compliance Gap Analysis", success, details, response.json() if success else response.text)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Compliance Gap Analysis", False, f"Exception: {str(e)}")
            return False, {}

    def test_get_documents(self):
        """Test get documents endpoint"""
        try:
            response = requests.get(f"{self.api_url}/documents", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Documents Retrieved: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Get Documents", success, details, f"Count: {len(data) if success else 0}")
            return success, response.json() if success else []
            
        except Exception as e:
            self.log_test("Get Documents", False, f"Exception: {str(e)}")
            return False, []

    def test_get_gaps(self):
        """Test get compliance gaps endpoint"""
        try:
            response = requests.get(f"{self.api_url}/gaps", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                gaps_count = len(data.get('gaps', []))
                details = f"Gaps Retrieved: {gaps_count}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Get Compliance Gaps", success, details, f"Gaps: {gaps_count if success else 0}")
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("Get Compliance Gaps", False, f"Exception: {str(e)}")
            return False, {}

    def test_get_mappings(self):
        """Test get clause mappings endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mappings", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Mappings Retrieved: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Get Clause Mappings", success, details, f"Count: {len(data) if success else 0}")
            return success, response.json() if success else []
            
        except Exception as e:
            self.log_test("Get Clause Mappings", False, f"Exception: {str(e)}")
            return False, []

    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting QSP Compliance Checker API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Health and system tests (as requested in review)
        print("🏥 Testing System Health...")
        health_success = self.test_health_check()
        
        # Basic connectivity tests
        print("📡 Testing Basic Connectivity...")
        api_available = self.test_api_root()
        
        if not api_available:
            print("❌ API not available. Stopping tests.")
            return False
        
        # Database and AI service tests (as requested in review)
        print("🗄️ Testing Database & AI Services...")
        db_success = self.test_database_connectivity()
        ai_success = self.test_ai_service()
        
        # Simple upload and list tests (as requested in review)
        print("📤 Testing Simple Upload & List...")
        simple_upload_success = self.test_document_upload_simple()
        list_docs_success = self.test_list_test_documents()
        
        # Dashboard test (should work even without data)
        print("📊 Testing Dashboard...")
        dashboard_success, dashboard_data = self.test_dashboard_endpoint()
        
        # Document upload tests
        print("📄 Testing Document Upload...")
        qsp_success, qsp_data = self.test_qsp_document_upload()
        iso_success, iso_data = self.test_iso_summary_upload()
        
        # Error handling test
        print("🚫 Testing Error Handling...")
        error_handling_success = self.test_invalid_file_upload()
        
        # Analysis tests (only if documents uploaded successfully)
        if qsp_success and iso_success:
            print("🤖 Testing AI Analysis...")
            print("   ⏳ Running clause mapping (this may take 30-60 seconds)...")
            mapping_success, mapping_data = self.test_clause_mapping_analysis()
            
            if mapping_success:
                print("   ⏳ Running compliance analysis...")
                compliance_success, compliance_data = self.test_compliance_gap_analysis()
            else:
                print("   ⚠️  Skipping compliance analysis due to mapping failure")
                compliance_success = False
        else:
            print("   ⚠️  Skipping AI analysis due to upload failures")
            mapping_success = False
            compliance_success = False
        
        # Data retrieval tests
        print("📋 Testing Data Retrieval...")
        docs_success, docs_data = self.test_get_documents()
        gaps_success, gaps_data = self.test_get_gaps()
        mappings_success, mappings_data = self.test_get_mappings()
        
        # Final dashboard check
        print("📊 Final Dashboard Check...")
        final_dashboard_success, final_dashboard_data = self.test_dashboard_endpoint()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        print()
        
        # Categorize results
        critical_failures = []
        warnings = []
        successes = []
        
        for result in self.test_results:
            if not result['success']:
                if any(keyword in result['test_name'].lower() for keyword in ['api root', 'dashboard', 'upload']):
                    critical_failures.append(result['test_name'])
                else:
                    warnings.append(result['test_name'])
            else:
                successes.append(result['test_name'])
        
        if critical_failures:
            print("🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   ❌ {failure}")
            print()
        
        if warnings:
            print("⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   ⚠️  {warning}")
            print()
        
        if successes:
            print("✅ SUCCESSFUL TESTS:")
            for success in successes:
                print(f"   ✅ {success}")
        
        print()
        
        # Overall assessment
        if success_rate >= 80:
            print("🎉 OVERALL: System is functioning well!")
            return True
        elif success_rate >= 60:
            print("⚠️  OVERALL: System has some issues but core functionality works")
            return True
        else:
            print("🚨 OVERALL: System has significant issues requiring attention")
            return False

def main():
    """Main test execution"""
    tester = QSPComplianceAPITester()
    
    try:
        success = tester.run_full_test_suite()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())