from collections import Counter
import re


class TextAnalyzer:

    def __init__(
        self,
        text: str,
        min_count: int = 1,
        stop_words: set[str] | None = None,
    ):
        """Initializes the text analyzer with optional minimum count filtering and stop words.

        :param text: Raw input string to analyze.
        :param min_count: Minimum frequency required to retain a token in results.
        :param stop_words: Set of words to ignore during analysis.
        """
        self.raw_text = text
        self.min_count = min_count
        self.stop_words = stop_words or set()
        self.tokens = self._tokenize(text)

    def _tokenize(self, text: str) -> list[str]:
        """Normalizes text to lowercase and extracts alphanumeric tokens."""
        return re.findall(r"\b\w+\b", text.lower())

    def get_frequencies(self) -> dict[str, int]:
        """Returns token frequencies filtered by stop words and minimum count threshold."""
        counts = Counter(
            token
            for token in self.tokens
            if token not in self.stop_words and not token.isdigit()
        )

        # Minimum-amount filtering step
        return {
            word: count
            for word, count in counts.items()
            if count >= self.min_count
        }

    def summary(self) -> dict[str, int]:
        """Calculates token and unique word statistics post-filtering."""
        filtered = self.get_frequencies()
        return {
            "total_raw_tokens": len(self.tokens),
            "filtered_unique_words": len(filtered),
            "filtered_total_count": sum(filtered.values()),
        }


# --- Usage Example ---
if __name__ == "__main__":
    sample = """
    Data science involves data collection, data cleaning, data analysis, and data visualization. 
    Data-driven decisions require good data quality. Clean data is key!
    """

    # Filter out tokens occurring less than 3 times
    analyzer = TextAnalyzer(text=sample, min_count=3, stop_words={"is", "and"})

    print("Filtered Frequencies (min_count >= 3):")
    print(analyzer.get_frequencies())

    print("\nSummary Statistics:")
    for metric, val in analyzer.summary().items():
        print(f"  {metric}: {val}")