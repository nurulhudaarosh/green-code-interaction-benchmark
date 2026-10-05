import re
from collections import Counter
from typing import Any, Dict, List, Tuple

def analyze_ngram_frequency(
    text: str, 
    top_k: int = 10,
    include_bigrams: bool = False
) -> Dict[str, Any]:
    """
    Analyzes unigram (and optionally bigram) frequency in a given text.
    
    Args:
        text: Input string to analyze.
        top_k: Number of most frequent tokens/n-grams to return.
        include_bigrams: If True, computes and includes bigram statistics.
        
    Returns:
        A dictionary containing:
          - 'total_tokens': Total word count.
          - 'unique_tokens': Number of distinct vocabulary items.
          - 'top_k': List of (word, count) tuples ordered by frequency.
          - 'total_bigrams': Total bigram count (only if include_bigrams=True).
          - 'top_k_bigrams': List of (bigram_tuple, count) (only if include_bigrams=True).
    """
    # Tokenize words, preserving contractions
    tokens = re.findall(r"\b\w+(?:'\w+)?\b", text.lower())
    
    unigram_counts = Counter(tokens)
    
    result: Dict[str, Any] = {
        "total_tokens": len(tokens),
        "unique_tokens": len(unigram_counts),
        "top_k": unigram_counts.most_common(top_k),
    }
    
    if include_bigrams:
        # Generate adjacent pairs: (w1, w2), (w2, w3), ...
        bigrams = list(zip(tokens[:-1], tokens[1:]))
        bigram_counts = Counter(bigrams)
        
        result["total_bigrams"] = len(bigrams)
        result["top_k_bigrams"] = bigram_counts.most_common(top_k)
        
    return result


# Example usage:
if __name__ == "__main__":
    sample_text = """
    Data science is the study of data. It involves developing methods of recording, 
    storing, and analyzing data to effectively extract useful information. Data science is 
    everywhere!
    """
    
    # 1. Unigram-only call (preserves original behavior)
    res_unigrams = analyze_ngram_frequency(sample_text, top_k=3)
    print("--- Unigrams Only ---")
    print(f"Total Tokens: {res_unigrams['total_tokens']}")
    print(f"Top Unigrams: {res_unigrams['top_k']}")

    # 2. Call with bigrams enabled
    res_bigrams = analyze_ngram_frequency(sample_text, top_k=3, include_bigrams=True)
    print("\n--- Including Bigrams ---")
    print(f"Total Bigrams: {res_bigrams['total_bigrams']}")
    print("Top Bigrams:")
    for (w1, w2), count in res_bigrams["top_k_bigrams"]:
        print(f"  - '{w1} {w2}': {count}")