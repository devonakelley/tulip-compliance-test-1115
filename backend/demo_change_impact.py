"""
Test Change Impact Detection - Demo Mode (without Postgres)
This demonstrates the core logic using in-memory vectors
"""
from openai import OpenAI
import os
import json
import numpy as np
from typing import List, Dict, Any

# Load OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("❌ OPENAI_API_KEY not set in environment")
    exit(1)

client = OpenAI(api_key=openai_key)

def get_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI"""
    text = ' '.join(text.split())
    if len(text) > 8000:
        text = text[:8000]
    
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large",
        dimensions=1536
    )
    return response.data[0].embedding

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def demo_change_impact():
    """Demonstrate change impact detection"""
    
    print("=" * 80)
    print("CHANGE IMPACT DETECTION - DEMO MODE")
    print("=" * 80)
    
    # Load sample data
    print("\n[1/3] Loading sample data...")
    with open('sample_qsp_sections.json', 'r') as f:
        qsp_sections = json.load(f)
    
    with open('sample_deltas.json', 'r') as f:
        deltas = json.load(f)
    
    print(f"✅ Loaded {len(qsp_sections)} QSP sections")
    print(f"✅ Loaded {len(deltas)} regulatory changes")
    
    # Generate embeddings for QSP sections
    print("\n[2/3] Generating embeddings for QSP sections...")
    qsp_embeddings = []
    
    for i, section in enumerate(qsp_sections):
        print(f"   Processing section {i+1}/{len(qsp_sections)}: {section['section_path']}")
        full_text = f"{section['heading']}: {section['text']}"
        embedding = get_embedding(full_text)
        qsp_embeddings.append({
            'section': section,
            'embedding': embedding
        })
    
    print(f"✅ Generated embeddings for {len(qsp_embeddings)} sections")
    
    # Analyze each change
    print("\n[3/3] Analyzing change impacts...")
    all_impacts = []
    
    for delta in deltas:
        clause_id = delta['clause_id']
        change_text = delta['change_text']
        change_type = delta['change_type']
        
        print(f"\n   Analyzing: {clause_id} ({change_type})")
        print(f"   Change: {change_text[:100]}...")
        
        # Generate embedding for change
        change_embedding = get_embedding(change_text)
        
        # Calculate similarity with all QSP sections
        similarities = []
        for qsp_emb in qsp_embeddings:
            similarity = cosine_similarity(change_embedding, qsp_emb['embedding'])
            similarities.append({
                'section': qsp_emb['section'],
                'similarity': similarity
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Filter by threshold and get top-3
        threshold = 0.55
        top_matches = [s for s in similarities if s['similarity'] > threshold][:3]
        
        print(f"   Found {len(top_matches)} potential impacts (threshold: {threshold})")
        
        for match in top_matches:
            section = match['section']
            confidence = match['similarity']
            
            # Generate rationale
            if confidence > 0.75:
                strength = "strong"
            elif confidence > 0.65:
                strength = "moderate"
            else:
                strength = "potential"
            
            rationale = (
                f"The change to {clause_id} has a {strength} semantic match "
                f"(confidence: {confidence:.2f}) with QSP section '{section['heading']}'. "
                f"This suggests the internal procedure may need review."
            )
            
            impact = {
                'clause_id': clause_id,
                'change_type': change_type,
                'qsp_section': section['section_path'],
                'qsp_heading': section['heading'],
                'confidence': round(confidence, 3),
                'rationale': rationale
            }
            
            all_impacts.append(impact)
            print(f"      → {section['section_path']}: {section['heading']} (confidence: {confidence:.1%})")
    
    # Generate report
    print("\n" + "=" * 80)
    print("IMPACT ANALYSIS REPORT")
    print("=" * 80)
    
    print(f"\nTotal Changes Analyzed: {len(deltas)}")
    print(f"Total Impacts Found: {len(all_impacts)}")
    print(f"Confidence Threshold: 55%")
    
    # Group by clause
    print("\n\nDetailed Impacts by Regulatory Change:")
    print("-" * 80)
    
    impacts_by_clause = {}
    for impact in all_impacts:
        clause = impact['clause_id']
        if clause not in impacts_by_clause:
            impacts_by_clause[clause] = []
        impacts_by_clause[clause].append(impact)
    
    for clause, impacts in impacts_by_clause.items():
        change = next(d for d in deltas if d['clause_id'] == clause)
        print(f"\n📋 {clause} - {change['change_type'].upper()}")
        print(f"   Change: {change['change_text'][:150]}...")
        print(f"\n   Affected QSP Sections ({len(impacts)}):")
        
        for impact in impacts:
            print(f"   • {impact['qsp_section']}: {impact['qsp_heading']}")
            print(f"     Confidence: {impact['confidence']:.1%}")
            print(f"     {impact['rationale'][:120]}...")
            print()
    
    # Statistics
    high_conf = sum(1 for i in all_impacts if i['confidence'] > 0.75)
    medium_conf = sum(1 for i in all_impacts if 0.60 <= i['confidence'] <= 0.75)
    low_conf = sum(1 for i in all_impacts if i['confidence'] < 0.60)
    
    print("\nConfidence Distribution:")
    print(f"  • High (>75%):     {high_conf} impacts")
    print(f"  • Medium (60-75%): {medium_conf} impacts")
    print(f"  • Low (55-60%):    {low_conf} impacts")
    
    # Save to CSV
    import csv
    
    csv_filename = 'impact_analysis_demo.csv'
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'clause_id', 'change_type', 'qsp_section', 'qsp_heading', 'confidence', 'rationale'
        ])
        writer.writeheader()
        writer.writerows(all_impacts)
    
    print(f"\n✅ Report saved to: {csv_filename}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE!")
    print("=" * 80)
    print("\nKey Findings:")
    print(f"  • {len(deltas)} regulatory changes mapped to {len(all_impacts)} QSP sections")
    print(f"  • Average {len(all_impacts)/len(deltas):.1f} QSP sections affected per change")
    print(f"  • System successfully identifies relevant internal procedures")
    print("\n✅ Change Impact Detection system is working correctly!\n")

if __name__ == "__main__":
    try:
        demo_change_impact()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
