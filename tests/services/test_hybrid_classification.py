#!/usr/bin/env python3
"""
Test script for hybrid classification system.
Tests various article types to verify keyword and AI classification.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.content_service import assign_topic

# Test cases
test_articles = [
    {
        "name": "HARD ACCEPT - Strong tech signals",
        "title": "New Python AI Features for Machine Learning and Cloud Computing",
        "summary": "Python 3.12 introduces groundbreaking features for artificial intelligence, machine learning, kubernetes deployment, and docker containerization.",
        "expected": "ACCEPT"
    },
    {
        "name": "HARD REJECT - Promotional content",
        "title": "Get Lifetime Netflix Subscription for $99",
        "summary": "Limited time offer! Lifetime subscription to Netflix and Hulu for only $99 (reg. $299). Don't miss out on this exclusive deal!",
        "expected": "REJECT"
    },
    {
        "name": "UNCERTAIN - Borderline (AI should decide)",
        "title": "New Developer Hiring Policy Announced",
        "summary": "Companies are adopting new policies for hiring software developers remotely. The policy focuses on skills rather than location.",
        "expected": "UNCERTAIN → AI decides"
    },
    {
        "name": "UNCERTAIN - Single tech keyword",
        "title": "Python Code Review Best Practices",
        "summary": "Learn how to conduct effective code reviews in your team. This guide covers communication, feedback, and collaboration strategies.",
        "expected": "UNCERTAIN → AI decides"
    },
    {
        "name": "HARD REJECT - Government policy",
        "title": "Housing Policy Review by Minister",
        "summary": "The National Development Minister announced a review of public housing policies, including income ceilings and eligibility criteria.",
        "expected": "REJECT"
    },
    {
        "name": "UNCERTAIN - Mixed signals",
        "title": "Tech Worker Salaries in Real Estate Market",
        "summary": "How software engineer salaries are affecting the real estate and housing market. Property prices rise as tech companies expand.",
        "expected": "UNCERTAIN → AI decides"
    }
]

def test_classification():
    """Run classification tests and display results."""
    print("=" * 80)
    print("HYBRID CLASSIFICATION SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Check if AI is enabled
    hf_enabled = bool(os.environ.get('HF_TOKEN'))
    print(f"🤖 AI Classification: {'ENABLED ✅' if hf_enabled else 'DISABLED ❌'}")
    print(f"   (HF_TOKEN {'is' if hf_enabled else 'is NOT'} set in environment)")
    print()
    print("=" * 80)
    print()
    
    results = []
    for i, test in enumerate(test_articles, 1):
        print(f"TEST {i}/{len(test_articles)}: {test['name']}")
        print(f"Title: {test['title']}")
        print(f"Expected: {test['expected']}")
        print("-" * 80)
        
        # Get classification with metadata
        topic, metadata = assign_topic(test['title'], test['summary'], return_metadata=True)
        
        # Display results
        if topic:
            print(f"✅ ACCEPTED")
            print(f"   Topic: {topic}")
        else:
            print(f"❌ REJECTED")
        
        print(f"   Method: {metadata.get('method', 'unknown')}")
        print(f"   AI Used: {metadata.get('ai_used', False)}")
        if metadata.get('confidence'):
            print(f"   Confidence: {metadata.get('confidence'):.2f}")
        print(f"   Reason: {metadata.get('reason', 'N/A')}")
        
        results.append({
            'test': test['name'],
            'accepted': topic is not None,
            'method': metadata.get('method'),
            'ai_used': metadata.get('ai_used')
        })
        
        print()
        print("=" * 80)
        print()
    
    # Summary
    print()
    print("SUMMARY")
    print("=" * 80)
    accepted = sum(1 for r in results if r['accepted'])
    rejected = len(results) - accepted
    ai_used = sum(1 for r in results if r['ai_used'])
    
    print(f"Total Tests: {len(results)}")
    print(f"Accepted: {accepted}")
    print(f"Rejected: {rejected}")
    print(f"AI Calls: {ai_used}")
    print()
    
    # Method distribution
    methods = {}
    for r in results:
        method = r['method']
        methods[method] = methods.get(method, 0) + 1
    
    print("Classification Methods:")
    for method, count in sorted(methods.items()):
        print(f"  - {method}: {count}")
    print()
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_classification()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
