#!/usr/bin/env python3
"""
Simple test for RAG components without ChromaDB
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_basic_components():
    """Test basic RAG components"""
    print("🧪 Testing Basic RAG Components")
    
    try:
        # Test embedding service
        print("\n📊 Testing Embedding Service...")
        from backend.rag.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        test_texts = [
            "Quality management system for medical devices",
            "Document control procedures and requirements",
            "Nonconforming product control processes"
        ]
        
        embeddings = await embedding_service.generate_embeddings(test_texts)
        print(f"✅ Generated {len(test_texts)} embeddings, shape: {embeddings.shape}")
        
        # Test similarity
        query = "medical device quality system"
        similar = await embedding_service.similarity_search(query, test_texts, top_k=2)
        print(f"✅ Similarity search returned {len(similar)} results")
        for i, result in enumerate(similar):
            print(f"   {i+1}. Score: {result['similarity_score']:.3f} - {result['text'][:50]}...")
        
        await embedding_service.cleanup()
        
        # Test document chunker
        print("\n📄 Testing Document Chunker...")
        from backend.rag.document_chunker import DocumentChunker
        
        chunker = DocumentChunker(max_chunk_tokens=200)
        
        test_qsp = {
            "_id": "qsp_test_001",
            "content": """
            Quality System Procedure QSP 4.2-1 Document Control
            
            1. PURPOSE
            This procedure defines the requirements for controlling documents in the quality management system.
            
            1.1 Scope
            This applies to all controlled documents including procedures, forms, and specifications.
            
            2. PROCEDURE
            2.1 Document Creation
            All documents must follow the established format and approval process.
            
            2.2 Document Review
            Documents shall be reviewed for adequacy before approval and use.
            
            2.3 Document Approval  
            The quality manager must approve all quality documents before release.
            
            3. RESPONSIBILITIES
            3.1 Document Controller
            Maintains the master list of controlled documents.
            
            3.2 Department Managers
            Ensure only current versions are used in their areas.
            """
        }
        
        chunks = await chunker.chunk_document(test_qsp)
        enhanced = chunker.enhance_chunk_metadata(chunks)
        
        print(f"✅ Created {len(chunks)} chunks from test QSP")
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: Section {chunk.section_number or 'N/A'} - {chunk.section_title or 'No title'}")
            print(f"   Tokens: {chunk.token_count}, Type: {chunk.chunk_type}")
            if chunk.metadata.get('content_themes'):
                print(f"   Themes: {chunk.metadata['content_themes']}")
        
        # Test impact analyzer (without database)
        print("\n🎯 Testing Impact Analysis Logic...")
        from backend.core.impact_analyzer import ImpactAnalyzer
        
        analyzer = ImpactAnalyzer()
        
        # Test alert generation
        test_change = {
            "clause_id": "4.2.3",
            "clause_title": "Document Control",
            "description": "New electronic document control requirements with version tracking"
        }
        
        test_impact = {
            "document_id": "qsp_4_2_1",
            "section_number": "2.1",
            "section_title": "Document Creation",
            "impact_level": "medium",
            "confidence_score": 0.85,
            "similarity_score": 0.78,
            "required_actions": ["Update document creation procedures", "Implement version tracking"],
            "compliance_risk": "Medium risk if not addressed within 6 months"
        }
        
        alerts = await analyzer._generate_specific_alerts(
            test_change, 
            {"impacts": [test_impact]}, 
            None
        )
        
        print(f"✅ Generated {len(alerts)} test alerts")
        if alerts:
            alert = alerts[0]
            print(f"   Alert: {alert['message'][:100]}...")
            print(f"   Priority: {alert['priority']}")
            print(f"   Actions: {len(alert['impact_details']['required_actions'])} required")
        
        print("\n🎉 Basic RAG components are working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def demonstrate_workflow():
    """Demonstrate the QSP compliance workflow"""
    print("\n🔄 Demonstrating QSP Compliance Workflow")
    
    print("""
    Workflow Overview:
    ================
    
    1. 📤 UPLOAD QSP DOCUMENTS
       • Medical device companies upload their 48 QSP files
       • Documents are parsed and chunked intelligently
       • Semantic embeddings are generated and stored
    
    2. 📋 UPLOAD REGULATORY CHANGES  
       • ISO 13485:2024 change summaries are uploaded
       • Changes are processed and embedded for search
    
    3. 🤖 AI-POWERED IMPACT ANALYSIS
       • RAG system finds relevant QSP sections for each change
       • Multi-model AI analyzes actual impact and confidence
       • System generates specific alerts with recommendations
    
    4. 📊 SPECIFIC ALERTS GENERATED
       • "ISO change detected that impacts QSP doc X in section X"
       • Clear identification of what needs to be updated
       • Prioritized action items for compliance teams
    
    Example Alert:
    "ISO change detected that impacts QSP 4.2-1 Document Control 
     in section 2.3 (Document Approval). Regulatory change in clause 
     4.2.3 (Document Control) requires review and potential updates."
    
    This RAG-powered system will provide:
    ✅ Accurate section-level impact identification
    ✅ High confidence scoring (threshold: 0.7+)
    ✅ Specific actionable recommendations
    ✅ Scalable processing of 48+ QSP documents
    ✅ Reliable regulatory change tracking
    """)

if __name__ == "__main__":
    async def main():
        print("🚀 Testing RAG-Powered QSP Compliance System\n")
        
        # Test basic components
        success = await test_basic_components()
        
        if success:
            await demonstrate_workflow()
            print("\n✅ RAG system components are ready!")
            print("\n📋 Next Steps:")
            print("   1. Start the full backend server with RAG endpoints")
            print("   2. Upload your QSP documents via API")
            print("   3. Process documents with /api/documents/{id}/process-rag")
            print("   4. Upload ISO change summaries")
            print("   5. Run /api/regulatory/analyze-impact for specific alerts")
            return 0
        else:
            print("\n❌ Component tests failed")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)