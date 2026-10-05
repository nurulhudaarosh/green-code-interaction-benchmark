import re
from collections import Counter
from typing import Iterable, List, Optional, Set, Tuple

# Standard minimal set of English stopwords
DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
    "you've", "your", "yours", "yourself", "yourselves"
}

class WordFrequencyAnalyzer:
    def __init__(self, stopwords: Optional[Iterable[str]] = None, min_word_len: int = 2):
        """
        Initializes the analyzer with custom or default stopwords.
        
        :param stopwords: Iterable of words to exclude. Defaults to DEFAULT_STOPWORDS.
        :param min_word_len: Minimum character length for tokens to be counted.
        """
        self.stopwords = set(stopwords) if stopwords is not None else DEFAULT_STOPWORDS
        # Normalize stopwords to lowercase
        self.stopwords = {w.lower() for w in self.stopwords}
        self.min_word_len = min_word_len
        # Regex extracts contiguous word characters, allowing internal hyphens/apostrophes
        self.token_pattern = re.compile(r"\b[a-zA-Z]+(?:['’][a-zA-Z]+)?\b")

    def tokenize(self, text: str) -> List[str]:
        """Extracts words from text, lowering case and stripping punctuation."""
        return [match.group(0).lower() for match in self.token_pattern.finditer(text)]

    def get_unigrams(self, text: str) -> List[str]:
        """Extracts unigrams filtered by length and stopword criteria."""
        tokens = self.tokenize(text)
        return [
            token for token in tokens 
            if len(token) >= self.min_word_len and token not in self.stopwords
        ]

    def analyze(self, text: str, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        Calculates frequencies and returns top-k most common unigrams.
        
        :param text: Raw input text string.
        :param top_k: Number of most frequent unigrams to return.
        :return: List of tuples (word, frequency).
        """
        unigrams = self.get_unigrams(text)
        counts = Counter(unigrams)
        return counts.most_common(top_k)


# Example usage
if __name__ == "__main__":
    sample_text = """
    Natural language processing (NLP) is a machine learning technology that gives
    computers the ability to interpret, manipulate, and comprehend human language.
    Organizations use massive volumes of voice and text data from various communication 
    channels like emails, text messages, social media newsHere is a clean, self-contained Python implementation using standard library modules (`re` and `collections.Counter`).