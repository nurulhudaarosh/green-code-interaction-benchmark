def run_boundary_tests():
    # Test 1: Single Vertex Graph (V=1, E=0)
    res = single_source_route_analyzer(1, [], 0)
    assert res == [0], f"Failed Test 1: {res}"

    # Test 2: Completely Disconnected Graph (V=4, E=0)
    res = single_source_route_analyzer(4, [], 0)
    assert res == [0, -1, -1, -1], f"Failed Test 2: {res}"

    # Test 3: Zero-Weight Edges & Cycles
    edges_zero = [(0, 1, 0), (1, 2, 0), (2, 0, 0), (1, 3, 5)]
    res = single_source_route_analyzer(4, edges_zero, 0)
    assert res == [0, 0, 0, 5], f"Failed Test 3: {res}"

    # Test 4: Large Edge Weights (w = 10^9)
    large_w = 10**9
    edges_large = [(0, 1, large_w), (1, 2, large_w)]
    res = single_source_route_analyzer(3, edges_large, 0)
    assert res == [0, 10**9, 2 * 10**9], f"Failed Test 4: {res}"

    # Test 5: Self-Loops and Multi-Edges
    edges_multi = [(0, 0, 10), (0, 1, 5), (0, 1, 2), (0, 1, 8)]
    res = single_source_route_analyzer(2, edges_multi, 0)
    assert res == [0, 2], f"Failed Test 5: {res}"

    # Test 6: Disconnected Multi-Component Graph
    edges_components = [(0, 1, 3), (2, 3, 4)]
    res, summary = single_source_route_analyzer(4, edges_components, 0, include_summary=True)
    assert res == [0, 3, -1, -1], f"Failed Test 6 distances: {res}"
    assert summary["settled_nodes"] == 2, f"Failed Test 6 settled count: {summary}"

    print("All boundary condition unit tests passed successfully!")

if __name__ == "__main__":
    run_boundary_tests()