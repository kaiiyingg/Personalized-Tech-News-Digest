#!/usr/bin/env python3
"""Test content filtering"""

from src.services.content_service import assign_topic

print("Testing improved content filtering...")

# Test with inappropriate content
result1 = assign_topic('Vibrator Review', 'Best adult products for personal pleasure')
print(f'Inappropriate content result: {result1}')

# Test with tech content
result2 = assign_topic('New AI Algorithm', 'Machine learning breakthrough in neural networks')
print(f'Tech content result: {result2}')

# Test with low tech content
result3 = assign_topic('Weather Update', 'Sunny skies expected tomorrow')
print(f'Weather content result: {result3}')

# Test with borderline tech content
result4 = assign_topic('Tech Company News', 'Google announces new software update')
print(f'Borderline tech content result: {result4}')

print("Testing complete!")
