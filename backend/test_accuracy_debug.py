import asyncio
import json
from core.change_impact_service_mongo import ChangeImpactServiceMongo

async def test_debug():
    service = ChangeImpactServiceMongo()
    
    with open('sample_deltas.json', 'r') as f:
        regulatory_changes = json.load(f)
    
    with open('sample_qsp_sections.json', 'r') as f:
        qsp_sections = json.load(f)
    
    tenant_id = "accuracy-test-debug"
    
    service.ingest_qsp_document(
        tenant_id=tenant_id,
        doc_id="test-debug-001",
        doc_name="Debug Test",
        sections=qsp_sections
    )
    
    result = await service.detect_impacts_async(
        tenant_id=tenant_id,
        deltas=regulatory_changes,
        top_k=5
    )
    
    print("Result keys:", result.keys())
    print("\nFirst impact:")
    if result['impacts']:
        print(json.dumps(result['impacts'][0], indent=2, default=str))

asyncio.run(test_debug())
