#!/usr/bin/env python
"""
Generate test files for comprehensive testing
"""

import os
import tempfile
from faker import Faker

def generate_test_files():
    """Generate various test files"""
    fake = Faker()
    
    test_dir = "tests/data/sample_files"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. Generate TXT files of different lengths
    txt_files = [
        ("short.txt", 100),      # 100 words
        ("medium.txt", 1000),    # 1000 words
        ("long.txt", 10000),     # 10000 words
        ("special_chars.txt", 500),  # With special characters
    ]
    
    for filename, word_count in txt_files:
        filepath = os.path.join(test_dir, filename)
        
        if "special" in filename:
            # Text with special characters
            text = fake.text(max_nb_chars=word_count * 6)
            text += "\n\nSpecial characters: ©®™€£¥•…—±×÷≠≈∞\n"
            text += "Code samples: def function():\n    return 'Hello'\n"
        else:
            # Regular text
            paragraphs = []
            for _ in range(max(1, word_count // 100)):
                paragraphs.append(fake.paragraph(nb_sentences=10))
            text = "\n\n".join(paragraphs)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Test Book: {filename}\n")
            f.write(f"Author: Test Author\n")
            f.write(f"Word Count: ~{word_count}\n")
            f.write("=" * 50 + "\n\n")
            f.write(text)
        
        print(f"✅ Generated {filename} ({word_count} words)")
    
    # 2. Create edge case files
    edge_cases = [
        ("empty.txt", ""),
        ("single_word.txt", "Hello"),
        ("only_numbers.txt", "12345 " * 100),
        ("unicode.txt", "Unicode test: ελληνικά, русский, 中文, 日本語, 한국어"),
    ]
    
    for filename, content in edge_cases:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Generated edge case: {filename}")
    
    print(f"\n📁 All test files generated in: {test_dir}")

if __name__ == "__main__":
    generate_test_files()