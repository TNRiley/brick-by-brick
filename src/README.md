# Pipeline

Run in order from this directory with Python 3.9+ (stdlib only; `python`, not `python3`, on Windows).

```bash
python fetch.py            # Rebrickable CSVs into .cache/ (~130 MB unzipped); --force to refetch
python build_payload.py    # counts pieces by colour, writes payload.json, prints checkpoints
python inject.py           # splices payload into template.html → ../index.html, wraps for Pages, adds catalog link
```

`payload.json` and `.cache/` are not committed. See `../REBUILD.md` for the decisions and expected values.
