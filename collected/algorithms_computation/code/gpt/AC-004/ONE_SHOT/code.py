from bisect import bisect_right


def weighted_interval_scheduling(jobs):
    """
    Solve the weighted interval scheduling problem.

    Input:
        jobs: list of (start, finish, profit)

    Rules:
        - A job i is compatible with job j when finish_i <= start_j.
        - Jobs touching at endpoints are therefore compatible.
        - Among maximum-profit solutions, choose the one whose sequence of
          original job indices is lexicographically smallest.

    Output:
        {
            "max_profit": maximum achievable profit,
            "selected_indices": original indices of the selected jobs
        }

    Notes:
        - Original indices are 0-based.
        - The solution is deterministic.
        - Uses sorting, binary search, and dynamic programming.
        - Standard library only.
    """

    n = len(jobs)

    if n == 0:
        return {
            "max_profit": 0,
            "selected_indices": []
        }

    # Store:
    # (start, finish, profit, original_index)
    sorted_jobs = [
        (start, finish, profit, index)
        for index, (start, finish, profit) in enumerate(jobs)
    ]

    # Sort primarily by finish time.
    # Original index is used as a deterministic secondary key.
    sorted_jobs.sort(key=lambda x: (x[1], x[3]))

    finishes = [job[1] for job in sorted_jobs]

    # p[i] = index of the last job finishing <= start of job i.
    predecessors = []
    for i, (start, _, _, _) in enumerate(sorted_jobs):
        p = bisect_right(finishes, start, 0, i) - 1
        predecessors.append(p)

    # dp[i] represents the best solution using sorted_jobs[0:i].
    #
    # Each entry is:
    #   (profit, tuple_of_original_indices)
    #
    # Keeping the index sequence explicitly makes tie-breaking deterministic.
    dp = [(0, ())]

    def better(candidate, current):
        """
        Compare two solutions.

        Higher profit wins.
        If profits tie, lexicographically smaller sequence of original
        indices wins.
        """
        candidate_profit, candidate_indices = candidate
        current_profit, current_indices = current

        if candidate_profit != current_profit:
            return candidate_profit > current_profit

        return candidate_indices < current_indices

    for i in range(n):
        start, finish, profit, original_index = sorted_jobs[i]

        # Option 1: skip this job.
        skip = dp[i]

        # Option 2: take this job.
        predecessor_solution = dp[predecessors[i] + 1]
        take_profit = predecessor_solution[0] + profit

        # The final selected-index sequence is kept sorted by original index
        # so that tie-breaking is based on the smallest original-index
        # sequence, independent of finish-time ordering.
        selected = list(predecessor_solution[1])
        selected.append(original_index)
        selected.sort()

        take = (take_profit, tuple(selected))

        dp.append(take if better(take, skip) else skip)

    best_profit, best_indices = dp[n]

    return {
        "max_profit": best_profit,
        "selected_indices": list(best_indices)
    }


if __name__ == "__main__":
    # Example:
    # Job 0: [1, 3], profit 50
    # Job 1: [3, 5], profit 20
    # Job 2: [2, 4], profit 70
    # Job 3: [5, 7], profit 30
    #
    # Jobs 0, 1, and 3 are compatible because endpoint touching is allowed.
    jobs = [
        (1, 3, 50),
        (3, 5, 20),
        (2, 4, 70),
        (5, 7, 30),
    ]

    result = weighted_interval_scheduling(jobs)
    print(result)