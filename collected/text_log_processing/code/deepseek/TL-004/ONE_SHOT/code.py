import re
from collections import Counter

def keyword_freq(paths, stopwords=(), top_k=20, include_bigrams=False):
    """
    Count keyword frequencies across one or more files.
    
    Args:
        paths: iterable of file paths (str or Path)
        stopwords: iterable of stopwords (case-insensitive)
        top_k: number of top terms to return
        include_bigrams: whether to also count adjacent bigrams
    
    Returns:
        dict with 'top' (list of (term, count) tuples) and 'total_tokens' (int)
    """
    token_re = re.compile(r'[a-z0-9]+')
    stop = {s.lower() for s in stopwords}
    
    unigrams = Counter()
    bigrams = Counter()
    total_tokens = 0
    
    prev_token = None  # for bigrams spanning lines/files
    
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    for match in token_re.finditer(line.lower()):
                        token = match.group()
                        if token in stop:
                            # A stopword breaks the bigram chain
                            prev_token = None
                            continue
                        
                        unigrams[token] += 1
                        total_tokens += 1
                        
                        if include_bigrams and prev_token is not None:
                            bigrams[(prev_token, token)] += 1
                        
                        prev_token = token
        except (IOError, OSError):
            # Skip unreadable files (including empty/nonexistent)
            continue
    
    counts = dict(unigrams)
    if include_bigrams:
        for (a, b), c in bigrams.items():
            counts[f"{a} {b}"] = c
    
    # Sort by count desc, then term asc
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    
    return {
        'top': ranked[:top_k],
        'total_tokens': total_tokens,
    }