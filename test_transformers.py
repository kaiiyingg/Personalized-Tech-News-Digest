#!/usr/bin/env python3
"""Test transformers installation"""

try:
    from transformers import pipeline
    print('✓ Transformers import successful!')
    
    summarizer = pipeline('summarization', model='t5-small')
    print('✓ Summarizer pipeline created successfully!')
    
    # Test summarization
    test_text = """
    Artificial intelligence technology continues to advance rapidly. 
    Machine learning models are becoming more sophisticated and capable of handling complex tasks. 
    Natural language processing has made significant strides in understanding human communication. 
    These developments are transforming industries and creating new opportunities for innovation.
    """
    
    result = summarizer(test_text, max_length=50, min_length=10, do_sample=False)
    print('✓ Summarization test successful!')
    print(f'Original length: {len(test_text)} characters')
    print(f'Summary: {result[0]["summary_text"]}')
    
except Exception as e:
    print(f'✗ Error: {e}')
    print('Please install transformers: pip install transformers')
