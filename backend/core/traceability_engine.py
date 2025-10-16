"""
Traceability Engine
Builds document hierarchy and performs impact analysis
"""
import logging
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.regulatory import DocumentType, RegulatoryFramework, DocumentHierarchy
from core.reference_extractor import reference_extractor

logger = logging.getLogger(__name__)

class TraceabilityEngine:
    """Build and analyze document traceability relationships"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def build_hierarchy(self, tenant_id: str) -> Dict[str, DocumentHierarchy]:
        """
        Build complete document hierarchy for tenant
        
        Returns:
            Dictionary of document_id -> DocumentHierarchy
        """
        hierarchy = {}
        
        # Get all documents with references
        doc_refs = await self.db.document_references.find(
            {"tenant_id": tenant_id}
        ).to_list(length=None)
        
        # Get all regulatory citations
        reg_citations = await self.db.regulatory_citations.find(
            {"tenant_id": tenant_id}
        ).to_list(length=None)
        
        # Build parent-child relationships
        parent_map = defaultdict(list)  # child -> [parents]
        child_map = defaultdict(list)   # parent -> [children]
        
        for ref in doc_refs:
            source = ref['source_doc_id']
            target = ref['target_doc_id']
            
            # Lower level implements higher level
            source_type = ref.get('source_doc_type')
            target_type = ref.get('target_doc_type')
            
            if source_type and target_type:
                source_level = reference_extractor.get_document_level(DocumentType(source_type))
                target_level = reference_extractor.get_document_level(DocumentType(target_type))
                
                if source_level > target_level:
                    # Source (lower level) implements target (higher level)
                    parent_map[source].append(target)
                    child_map[target].append(source)
                else:
                    # Target (lower level) implements source (higher level)
                    parent_map[target].append(source)
                    child_map[source].append(target)
        
        # Group citations by document
        citations_by_doc = defaultdict(list)
        for cit in reg_citations:
            doc_id = cit['document_id']
            citations_by_doc[doc_id].append({
                'framework': cit['framework'],
                'clause_id': cit['clause_id'],
                'citation': cit['citation']
            })
        
        # Build hierarchy objects
        all_doc_ids = set(parent_map.keys()) | set(child_map.keys())
        
        for doc_id in all_doc_ids:
            # Determine doc type and level
            doc_type = reference_extractor.determine_document_type(doc_id)
            if not doc_type:
                doc_type = DocumentType.REFERENCE_DOC
            
            level = reference_extractor.get_document_level(doc_type)
            
            # Extract implements clauses
            implements_clauses = []
            for cit in citations_by_doc.get(doc_id, []):
                implements_clauses.append({
                    'framework': cit['framework'],
                    'clause_id': cit['clause_id']
                })
            
            hierarchy[doc_id] = DocumentHierarchy(
                tenant_id=tenant_id,
                document_id=doc_id,
                document_name=doc_id,  # Can be enhanced with actual names
                document_type=doc_type,
                level=level,
                parent_docs=list(set(parent_map.get(doc_id, []))),
                child_docs=list(set(child_map.get(doc_id, []))),
                regulatory_citations=[c['citation'] for c in citations_by_doc.get(doc_id, [])],
                implements_clauses=implements_clauses
            )
        
        return hierarchy
    
    async def find_impacted_documents(
        self,
        tenant_id: str,
        changed_doc_id: str,
        direction: str = "downstream"
    ) -> Dict[str, Set[str]]:
        """
        Find all documents impacted by a change
        
        Args:
            tenant_id: Tenant ID
            changed_doc_id: Document that changed
            direction: "downstream" (what implements this) or "upstream" (what this implements)
            
        Returns:
            {level: set of doc_ids} dictionary
        """
        hierarchy = await self.build_hierarchy(tenant_id)
        
        if changed_doc_id not in hierarchy:
            return {}
        
        impacted = defaultdict(set)
        visited = set()
        queue = deque([changed_doc_id])
        
        while queue:
            current_id = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id in hierarchy:
                current_doc = hierarchy[current_id]
                level = current_doc.level
                
                if current_id != changed_doc_id:
                    impacted[level].add(current_id)
                
                # Get next documents based on direction
                if direction == "downstream":
                    # Find documents that implement this one (child docs)
                    next_docs = current_doc.child_docs
                else:  # upstream
                    # Find documents this implements (parent docs)
                    next_docs = current_doc.parent_docs
                
                for doc_id in next_docs:
                    if doc_id not in visited:
                        queue.append(doc_id)
        
        return dict(impacted)
    
    async def find_regulatory_impact(
        self,
        tenant_id: str,
        framework: RegulatoryFramework,
        clause_id: str
    ) -> List[Dict[str, any]]:
        """
        Find all documents that implement a specific regulatory clause
        
        Returns:
            List of {document_id, document_type, level, citation}
        """
        # Find all citations for this clause
        citations = await self.db.regulatory_citations.find({
            "tenant_id": tenant_id,
            "framework": framework.value,
            "clause_id": clause_id
        }).to_list(length=None)
        
        # Build hierarchy to get document info
        hierarchy = await self.build_hierarchy(tenant_id)
        
        results = []
        for cit in citations:
            doc_id = cit['document_id']
            if doc_id in hierarchy:
                doc = hierarchy[doc_id]
                results.append({
                    'document_id': doc_id,
                    'document_type': doc.document_type.value,
                    'level': doc.level,
                    'citation': cit['citation'],
                    'context': cit.get('context', '')
                })
        
        return sorted(results, key=lambda x: x['level'])
    
    async def build_compliance_matrix(
        self,
        tenant_id: str
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Build compliance matrix showing which documents implement which regulations
        
        Returns:
            {framework: {clause_id: [doc_ids]}}
        """
        citations = await self.db.regulatory_citations.find({
            "tenant_id": tenant_id
        }).to_list(length=None)
        
        matrix = defaultdict(lambda: defaultdict(list))
        
        for cit in citations:
            framework = cit['framework']
            clause_id = cit['clause_id']
            doc_id = cit['document_id']
            
            if doc_id not in matrix[framework][clause_id]:
                matrix[framework][clause_id].append(doc_id)
        
        # Convert to regular dict
        return {
            fw: dict(clauses) for fw, clauses in matrix.items()
        }
    
    async def get_hierarchy_tree(self, tenant_id: str) -> Dict[str, any]:
        """
        Get hierarchical tree structure for visualization
        
        Returns:
            Nested tree structure
        """
        hierarchy = await self.build_hierarchy(tenant_id)
        
        # Group by level
        by_level = defaultdict(list)
        for doc_id, doc in hierarchy.items():
            by_level[doc.level].append({
                'id': doc_id,
                'name': doc.document_name,
                'type': doc.document_type.value,
                'level': doc.level,
                'parent_docs': doc.parent_docs,
                'child_docs': doc.child_docs,
                'regulatory_citations': doc.regulatory_citations[:5],  # Limit for display
                'citation_count': len(doc.regulatory_citations)
            })
        
        # Build tree structure
        tree = {
            'levels': sorted(by_level.keys()),
            'documents_by_level': dict(by_level),
            'total_documents': len(hierarchy),
            'total_relationships': sum(len(doc.child_docs) for doc in hierarchy.values())
        }
        
        return tree
    
    async def analyze_coverage_gaps(
        self,
        tenant_id: str,
        framework: RegulatoryFramework
    ) -> Dict[str, any]:
        """
        Analyze regulatory coverage and identify gaps
        
        Returns:
            {covered_clauses, uncovered_clauses, coverage_percentage}
        """
        from core.regulatory_knowledge_base import get_clauses_by_framework
        
        # Get all clauses for framework
        all_clauses = get_clauses_by_framework(framework)
        all_clause_ids = {c.clause_id for c in all_clauses}
        
        # Get implemented clauses
        citations = await self.db.regulatory_citations.find({
            "tenant_id": tenant_id,
            "framework": framework.value
        }).to_list(length=None)
        
        implemented_clause_ids = {cit['clause_id'] for cit in citations if cit.get('clause_id')}
        
        # Calculate gaps
        uncovered = all_clause_ids - implemented_clause_ids
        covered = all_clause_ids & implemented_clause_ids
        
        coverage_pct = (len(covered) / len(all_clause_ids) * 100) if all_clause_ids else 0
        
        # Get details for uncovered clauses
        uncovered_details = [
            {
                'clause_id': c.clause_id,
                'title': c.title,
                'criticality': c.criticality,
                'category': c.category
            }
            for c in all_clauses if c.clause_id in uncovered
        ]
        
        return {
            'framework': framework.value,
            'total_clauses': len(all_clause_ids),
            'covered_clauses': len(covered),
            'uncovered_clauses': len(uncovered),
            'coverage_percentage': round(coverage_pct, 2),
            'uncovered_details': sorted(uncovered_details, key=lambda x: x['criticality'], reverse=True)
        }
