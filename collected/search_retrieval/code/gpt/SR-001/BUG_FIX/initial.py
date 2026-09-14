from collections import defaultdict

class InvertedIndex:
    def __init__(self, documents):
        """
        documents: mapping of document_id -> text
                   e.g. {1: "the quick brown fox", 2: "quick red fox"}
        """
        self.documents = documents
        self.index = defaultdict(set)

        # Build the inverted index.
        for doc_id, text in documents.items():
            for keyword in self._tokenize(text):
                self.index[keyword].add(doc_id)

    @staticmethod
    def _tokenize(text):
        """Normalize text into keywords."""
        return text.lower().split()

    def query(self, query_text):
        """
        Return document IDs containing ALL keywords in query_text.

        Results are deterministic and sorted by document ID.
        """
        keywords = self._tokenize(query_text)

        if not keywords:
            return []

        # Start with the postings list for the first keyword,
        # then intersect with the remaining keywords.
        result = self.index.get(keywords[0], set()).copy()

        for keyword in keywords[1:]:
            result.intersection_update(self.index.get(keyword, set()))

            if not result:
                break

        return sorted(result)


# Example usage
documents = {
    1: "the quick brown fox",
    2: "the quick red fox",
    3: "lazy brown dog",
    4: "quick brown dog",
}

index = InvertedIndex(documents)

print(index.query("quick"))
# [1, 2, 4]

print(index.query("quick fox"))
# [1, 2]

print(index.query("brown dog"))
# [3, 4]

print(index.query("quick brown"))
# [1, 4]

print(index.query("quick blue"))
# []