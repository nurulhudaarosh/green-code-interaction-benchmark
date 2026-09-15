# Test case showing the bug
packages = ["A", "B", "C", "D"]
deps = [
    ("C", "A"),  # C depends on A
    ("C", "B"),  # C depends on B  
    ("D", "C")   # D depends on C
]

# Expected: Levels = 3 (A/B at level 0, C at level 1, D at level 2)
# Current bug: Returns Levels = 2 (incorrect!)