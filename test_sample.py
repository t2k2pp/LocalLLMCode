#!/usr/bin/env python3
"""Test file for code analysis"""

import unused_module
import os
import sys

def overly_long_function_that_needs_refactoring():
    """This function is intentionally long to trigger warnings"""
    magic_number = 42
    another_magic = 100
    yet_another = 500
    
    # Simulate a long function
    data = []
    for i in range(magic_number):
        if i % 2 == 0:
            data.append(i * another_magic)
        else:
            data.append(i + yet_another)
    
    # More processing
    results = []
    for item in data:
        if item > 1000:
            results.append(item * 2)
        elif item > 500:
            results.append(item * 1.5)
        else:
            results.append(item)
    
    # Final processing
    total = 0
    for result in results:
        total += result
    
    # Print results (console.log equivalent)
    print(f"Total calculated: {total}")
    print(f"Data points: {len(data)}")
    print(f"Results: {len(results)}")
    
    return total

class ExampleClass:
    """Example class with some issues"""
    
    def __init__(self):
        self.value = 999  # Another magic number
        self.data = []
    
    def process_data(self):
        for i in range(50):  # Magic number here too
            self.data.append(i * 3)  # And here

if __name__ == "__main__":
    obj = ExampleClass()
    result = overly_long_function_that_needs_refactoring()
    print(f"Final result: {result}")