import re
from collections import Counter
from typing import Dict, List, Tuple, Union

def analyze_unigram_frequency(
    text: str, 
    top_k: int = 10
) -> Dict[str, Union[int, List[Tuple[str, int]]]]:
    """
    Analyzes unigram (single-word) frequency in a given text.
    
    Args:
        text: Input string to analyze.
        top_k: Number of most frequent tokens to return.
        
    Returns:
        A dictionary containing:
          - 'total_tokens': Total word count.
          - 'unique_tokens': Number of distinct vocabulary items.
          - 'top_k': List of (word, count) tuples ordered by frequency.
    """
    # Extract alphanumeric words (handles basic punctuation and contractions)
    # \b\w+\b captures whole words; lowercasing ensures case-insensitivity
    tokens = re.findall(r"\b\w+(?:'\w+)?\b", text.lower())
    
    counts = Counter(tokens)
    
    return {
        "total_tokens": len(tokens),
        "unique_tokens": len(counts),
        "top_k": counts.most_most_common(top_k) if hasattr(counts, "most_most_common") else counts.most_common(top_k)
    }


# Example usage:
if __name__ == "__main__":
    sample_text = """
    Data science is the study of data. It involves developing methods of recording, 
    storing, and analyzing data to effectively extract useful information. Data is 
    everywhere!
    """
    
    result = analyze_unigram_frequency(sample_text, top_k=5)
    
    print(f"Total Tokens:  {result['total_tokens']}")
    print(f"Unique Tokens: {result['unique_tokens']}")
    print("\nTop Words:")
    for word, freq in result["top_k"]:
        print(f"  - {word}: {freq}")