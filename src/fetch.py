"""Download the Rebrickable catalogue tables into src/.cache/ and unzip them.

Rebrickable publishes these daily and allows use for any purpose with attribution,
but asks that automated downloads happen at most once a day. So an existing file is
kept unless --force is passed.
"""
import gzip, pathlib, shutil, sys, urllib.request

TABLES = ["colors", "themes", "sets", "inventories", "inventory_parts"]
BASE = "https://cdn.rebrickable.com/media/downloads/{}.csv.gz"
CACHE = pathlib.Path(__file__).resolve().parent / ".cache"


def main():
    force = "--force" in sys.argv
    CACHE.mkdir(exist_ok=True)
    for t in TABLES:
        out = CACHE / f"{t}.csv"
        if out.exists() and not force:
            print(f"{t}: cached")
            continue
        gz = CACHE / f"{t}.csv.gz"
        req = urllib.request.Request(BASE.format(t), headers={"User-Agent": "brick-by-brick/1.0"})
        with urllib.request.urlopen(req) as r, open(gz, "wb") as f:
            shutil.copyfileobj(r, f)
        with gzip.open(gz, "rb") as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst)
        gz.unlink()
        print(f"{t}: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
