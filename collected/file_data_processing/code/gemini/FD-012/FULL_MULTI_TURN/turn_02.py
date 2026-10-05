from collections import Counter
import re

word_pattern = re.compile(r"[a-zA-Z]+")

# Simulated document with repeated words
doc_content = "apple apple banana apple cherry banana"

words = word_pattern.findall(doc_content.lower())

total_counts = Counter()
doc_frequencies = Counter()

# Updates
total_counts.update(words)  # All occurrences
doc_frequencies.update(set(words))  # Set removes duplicates per file

print(f"Total count for 'apple': {total_counts['apple']}")  # Output: 3
print(
    f"Doc frequency for 'apple': {doc_frequencies['apple']}"
)  # Output: 1