from collections import Counter
import re


class TextAnalyzer:

    def __init__(
        self,
        text: str,
        min_count: int = 1,
        stop_words: set[str] | None = None,
    ):
        """Initializes analyzer with text, minimum count threshold, and optional stop words."""
        self.raw_text = text
        self.min_count = min_count
        self.stop_words = stop_words or set()
        self.tokens = self._tokenize(text)

    def _tokenize(self, text: str) -> list[str]:
        """Normalizes text to lowercase and extracts alphanumeric tokens."""
        return re.findall(r"\b\w+\b", text.lower())

    def get_frequencies(self) -> dict[str, int]:
        """Calculates word frequencies and applies minimum threshold filtering."""
        counts = Counter(
            token
            for token in self.tokens
            if token not in self.stop_words and not token.isdigit()
        )

        # Minimum-amount filtering
        return {
            word: count
            for word, count in counts.items()
            if count >= self.min_count
        }

    def summary(self) -> dict[str, int]:
        """Computes summary metrics post-filtering."""
        filtered_freqs = self.get_frequencies()
        return {
            "total_tokens": len(self.tokens),
            "filtered_unique_words": len(filtered_freqs),
            "filtered_total_count": sum(filtered_freqs.values()),
        }


if __name__ == "__main__":
    sample_text = """
    Data science involves data collection, data cleaning, data analysis, and data visualization. 
    Data-driven decisions require good data quality. Clean data is key!
    """

    # Keep tokens appearing at least 3 times, ignoring specific stop words
    analyzer = TextAnalyzer(
        text=sample_text, min_count=3, stop_words={"is", "and"}
    )

    print("Filtered Word Counts (min_count >= 3):")
    print(analyzer.get_frequencies())

    print("\nSummary Statistics:")
    for metric, value in analyzer.summary().items():
        print(f"  {metric}: {value}")