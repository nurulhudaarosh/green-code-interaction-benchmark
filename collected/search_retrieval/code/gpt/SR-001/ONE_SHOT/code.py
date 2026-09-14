from collections import defaultdict
class InvertedIndexSearchEngine:
    def __init__(self, documents):
        """
        Build an inverted index.
        documents: list[str]
        Internal structure:
            keyword -> sorted list of document IDs
        """
        self.index = defaultdict(list)
        if not documents:
            return
        for doc_id, document in enumerate(documents):
            if not document:
                continue
            # A keyword should occur at most once per document.
            keywords = set(document.lower().split())
            for keyword in keywords:
                self.index[keyword].append(doc_id)
    def search(self, query):
        """
        Search for documents containing ALL keywords.
        Returns:
            list[int] -- matching document IDs in ascending order
        """
        # Empty query
        if not query or not query.strip():
            return []
        keywords = set(query.lower().split())
        if not keywords:
            return []
        posting_lists = []
        # Index lookup: no full document scan.
        for keyword in keywords:
            postings = self.index.get(keyword)
            if not postings:
                return []
            posting_lists.append(postings)
        # Intersect the smallest posting list first.
        posting_lists.sort(key=len)
        result = posting_lists[0][:]
        for postings in posting_lists[1:]:
            result = self._intersect(result, postings)
            if not result:
                break
        return result
    @staticmethod
    def _intersect(a, b):
        """
        Intersect two sorted posting lists using two pointers.
        """
        i = 0
        j = 0
        result = []
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                result.append(a[i])
                i += 1
                j += 1
            elif a[i] < b[j]:
                i += 1
            else:
                j += 1
        return result
def build_inverted_index(documents):
    """
    Build and return the search engine.
    """
    return InvertedIndexSearchEngine(documents)

Example

documents = [
    "machine learning is useful",
    "machine learning algorithms",
    "deep learning algorithms",
    "machine vision",
    "learning algorithms are powerful"
]
engine = build_inverted_index(documents)
print(engine.search("machine"))
# [0, 1, 3]
print(engine.search("learning"))
# [0, 1, 2, 4]
print(engine.search("machine learning"))
# [0, 1]
print(engine.search("learning algorithms"))
# [1, 2, 4]
print(engine.search("machine learning algorithms"))
# [1]
print(engine.search(""))
# []
print(engine.search("unknown"))
# []