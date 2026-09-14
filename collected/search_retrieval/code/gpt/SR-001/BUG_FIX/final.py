from collections import defaultdict


class InvertedIndex:
    def __init__(self, documents=None):
        """
        documents: mapping of document_id -> text

        Example:
            {
                1: "the quick brown fox",
                2: "quick red fox",
            }
        """
        self.index = defaultdict(list)

        if not documents:
            return

        # Build the index once.
        for doc_id, text in documents.items():
            keywords = set(self._tokenize(text))

            for keyword in keywords:
                self.index[keyword].append(doc_id)

        # Store postings in deterministic order.
        for keyword in self.index:
            self.index[keyword].sort()

    @staticmethod
    def _tokenize(text):
        if not text:
            return []
        return text.lower().split()

    def query(self, query_text=None):
        """
        Return IDs of documents containing ALL query keywords.

        The returned list is always deterministic.
        Queries never mutate the index.
        """
        keywords = self._tokenize(query_text)

        # Empty query -> empty result.
        if not keywords:
            return []

        # Remove duplicate keywords while preserving normalized identity.
        keywords = set(keywords)

        # If any keyword isn't indexed, the AND result is empty.
        postings = []
        for keyword in keywords:
            posting = self.index.get(keyword)
            if not posting:
                return []
            postings.append(posting)

        # Intersect the smallest posting lists first.
        postings.sort(key=len)

        result = set(postings[0])

        for posting in postings[1:]:
            result.intersection_update(posting)

            if not result:
                return []

        # Never return the internal set or rely on set iteration order.
        return sorted(result)


# Example
documents = {
    1: "the quick brown fox",
    2: "the quick red fox",
    3: "lazy brown dog",
    4: "quick brown dog",
}

index = InvertedIndex(documents)

assert index.query("quick") == [1, 2, 4]
assert index.query("quick fox") == [1, 2]
assert index.query("brown dog") == [3, 4]
assert index.query("quick brown") == [1, 4]

# Empty collection
empty_index = InvertedIndex({})
assert empty_index.query("quick") == []
assert empty_index.query("") == []
assert empty_index.query(None) == []

# Repeated queries are deterministic and non-mutating
assert index.query("quick brown") == [1, 4]
assert index.query("quick brown") == [1, 4]
assert index.query("quick brown") == [1, 4]

# Duplicate query terms don't change the result
assert index.query("quick quick") == [1, 2, 4]