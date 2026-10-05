No code change was needed. `logs_to_csv` already writes the header before it reads any lines, so empty input and filters that match nothing both produce a header-only CSV. I confirmed it with four runs, and `csv.DictReader` reads each output as a valid CSV with 0 rows:

- An empty file wrote a one-line CSV with just the header.
- A file containing only blank lines produced the same header-only CSV.
- `--method DELETE` matched nothing and produced a header-only CSV (`written=0 skipped=3 filtered=5`).
- `--status-class 1xx` matched nothing and also produced a header-only CSV (`written=0 skipped=3 filtered=5`).

One case I didn't test is a missing input file, which raises `FileNotFoundError` before any CSV is created. I left that as is, since silently writing an empty CSV for a wrong path would hide the mistake.