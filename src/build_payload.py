"""Turn the Rebrickable tables into src/payload.json for the page.

Decisions (all explained in REBUILD.md):
- one inventory per set: version 1
- spare parts excluded; minifigure inventories are not followed, so minifig parts are out
- root themes Modulex, Books, Gear and Service Packs excluded (not LEGO building sets,
  or replacement parts rather than sets), and the "Database Sets" theme under Other, which
  holds Rebrickable's placeholder records for loose parts (Modulex, HO-scale), not real sets
- colours [Unknown] (-1) and [No Color/Any Color] (9999) dropped
- the last complete year is 2025; 2026 is carried and flagged partial; 2027 dropped
"""
import base64, collections, csv, json, math, pathlib, struct

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / ".cache"
LAST_YEAR = 2026
EXCLUDE_ROOTS = {"Modulex", "Books", "Gear", "Service Packs"}
EXCLUDE_THEMES = {"Database Sets"}
DROP_COLOURS = {"-1", "9999"}

CLASSIC = {"Red", "Yellow", "Blue", "White", "Black", "Green"}
OLD_GREY = {"Light Gray", "Dark Gray"}
NEW_GREY = {"Light Bluish Gray", "Dark Bluish Gray"}
OTHER_GREY = {"Very Light Gray", "Very Light Bluish Gray"}
EARTH = {"Tan", "Dark Tan", "Brown", "Reddish Brown", "Dark Brown", "Light Brown", "Medium Brown",
         "Nougat", "Light Nougat", "Medium Nougat", "Dark Nougat", "Warm Tan", "Sienna Brown",
         "Umber Brown", "Fabuland Brown"}
SHINY_WORDS = ("Pearl", "Chrome", "Metallic", "Metal", "Flat Silver", "Flat Dark Gold", "Speckle",
               "Two-tone", "Copper", "Glitter", "Opal")


def rows(name):
    with open(CACHE / f"{name}.csv", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def family(c):
    n = c["name"]
    if c["is_trans"] == "True" or n.startswith(("Trans-", "Glitter Trans", "Opal Trans")):
        return "trans"
    if any(w in n for w in SHINY_WORDS):
        return "shiny"
    if n in CLASSIC:
        return "classic"
    if n in OLD_GREY or n in NEW_GREY or n in OTHER_GREY:
        return "grey"
    if n in EARTH:
        return "earth"
    return "other"


def b64(fmt, values):
    return base64.b64encode(struct.pack(f"<{len(values)}{fmt}", *values)).decode("ascii")


def main():
    themes = {r["id"]: r for r in rows("themes")}

    def root(tid):
        while themes[tid]["parent_id"]:
            tid = themes[tid]["parent_id"]
        return tid

    sets = {}
    for r in rows("sets"):
        y = int(r["year"])
        if (y > LAST_YEAR or themes[root(r["theme_id"])]["name"] in EXCLUDE_ROOTS
                or themes[r["theme_id"]]["name"] in EXCLUDE_THEMES):
            continue
        sets[r["set_num"]] = r

    inv = {r["id"]: r["set_num"] for r in rows("inventories")
           if r["version"] == "1" and r["set_num"] in sets}

    per_set = collections.defaultdict(collections.Counter)
    for r in rows("inventory_parts"):
        if r["is_spare"] == "True" or r["color_id"] in DROP_COLOURS:
            continue
        s = inv.get(r["inventory_id"])
        if s:
            per_set[s][r["color_id"]] += int(r["quantity"])

    # colours actually used, ordered for stacking: family, then lightness
    raw_colours = {r["id"]: r for r in rows("colors")}
    used = collections.Counter()
    for c in per_set.values():
        used.update(c)
    fam_order = ["grey", "classic", "earth", "other", "shiny", "trans"]
    classic_order = ["Black", "Blue", "Green", "Red", "Yellow", "White"]
    grey_order = ["Dark Gray", "Dark Bluish Gray", "Light Gray", "Light Bluish Gray",
                  "Very Light Gray", "Very Light Bluish Gray"]

    def hue_key(c):
        rgb = c["rgb"]
        r, g, b = (int(rgb[i:i + 2], 16) / 255 for i in (0, 2, 4))
        mx, mn = max(r, g, b), min(r, g, b)
        light = (mx + mn) / 2
        if mx == mn:
            h = 0
        elif mx == r:
            h = ((g - b) / (mx - mn)) % 6
        elif mx == g:
            h = (b - r) / (mx - mn) + 2
        else:
            h = (r - g) / (mx - mn) + 4
        return (h, light)

    def sort_key(cid):
        c = raw_colours[cid]
        f = family(c)
        if f == "classic":
            k = (classic_order.index(c["name"]),)
        elif f == "grey":
            k = (grey_order.index(c["name"]),)
        else:
            k = hue_key(c)
        return (fam_order.index(f), k)

    colour_ids = sorted(used, key=sort_key)
    cidx = {cid: i for i, cid in enumerate(colour_ids)}

    # first/last year each colour appears, by pieces in that year's sets
    first, last = {}, {}
    year_pieces = collections.defaultdict(collections.Counter)
    year_setshare = collections.defaultdict(lambda: collections.defaultdict(float))
    year_sets = collections.Counter()
    for s, c in per_set.items():
        y = int(sets[s]["year"])
        tot = sum(c.values())
        year_sets[y] += 1
        for cid, q in c.items():
            year_pieces[y][cid] += q
            year_setshare[y][cid] += q / tot
            first[cid] = min(first.get(cid, 9999), y)
            last[cid] = max(last.get(cid, 0), y)

    colours = [{
        "name": raw_colours[cid]["name"],
        "rgb": raw_colours[cid]["rgb"].upper(),
        "fam": family(raw_colours[cid]),
        "pieces": used[cid],
        "sets": sum(1 for c in per_set.values() if cid in c),
        "first": first[cid],
        "last": last[cid],
    } for cid in colour_ids]

    years = list(range(min(year_sets), LAST_YEAR + 1))
    year_rows = []
    for y in years:
        pc = year_pieces.get(y, {})
        ss = year_setshare.get(y, {})
        year_rows.append({
            "y": y,
            "sets": year_sets.get(y, 0),
            "pieces": sum(pc.values()),
            # sparse [colourIndex, pieces, setShareSum×1000 rounded]
            "c": sorted([[cidx[k], v, round(ss[k] * 1000)] for k, v in pc.items()]),
        })

    # themes: roots with at least 40 sets that have parts, excluding catch-alls
    CATCHALL = {"Other", "Promotional", "LEGO Brand Store", "LEGO Exclusive", "Seasonal",
                "Educational and Dacta", "Universal Building Set", "Bulk Bricks", "Classic",
                "System", "Make & Create", "Freestyle", "Legoland", "Legoland Parks",
                "BrickLink Designer Program", "Games", "Collectible Minifigures", "Sports",
                "FIRST LEGO League", "LEGO Ideas and CUUSOO", "Icons"}
    theme_pieces = collections.defaultdict(collections.Counter)
    theme_sets = collections.Counter()
    theme_years = collections.defaultdict(list)
    for s, c in per_set.items():
        rt = themes[root(sets[s]["theme_id"])]["name"]
        theme_pieces[rt].update(c)
        theme_sets[rt] += 1
        theme_years[rt].append(int(sets[s]["year"]))
    theme_rows = []
    for name, n in theme_sets.items():
        if n < 40 or name in CATCHALL:
            continue
        ys = sorted(theme_years[name])
        theme_rows.append({
            "name": name, "sets": n, "pieces": sum(theme_pieces[name].values()),
            "from": ys[0], "to": ys[-1],
            "c": sorted([[cidx[k], v] for k, v in theme_pieces[name].items()], key=lambda x: -x[1]),
        })
    theme_rows.sort(key=lambda t: -t["pieces"])

    # set search table, only sets with parts
    theme_names, tn_index = [], {}

    def tname(tid):
        rt = themes[root(tid)]["name"]
        leaf = themes[tid]["name"]
        label = rt if leaf == rt else f"{rt} · {leaf}"
        if label not in tn_index:
            tn_index[label] = len(theme_names)
            theme_names.append(label)
        return tn_index[label]

    order = sorted(per_set, key=lambda s: (int(sets[s]["year"]), s))
    nums, names, yrs, tids, offs, ci, qty = [], [], [], [], [0], [], []
    for s in order:
        r = sets[s]
        nums.append(s)
        names.append(r["name"])
        yrs.append(int(r["year"]) - years[0])
        tids.append(tname(r["theme_id"]))
        for cid, q in sorted(per_set[s].items(), key=lambda kv: -kv[1]):
            assert q < 65536, (s, cid, q)
            ci.append(cidx[cid])
            qty.append(q)
        offs.append(len(ci))

    payload = {
        "built": "2026-09-16",
        "firstYear": years[0],
        "lastYear": LAST_YEAR,
        "partialYear": LAST_YEAR,
        "colours": colours,
        "years": year_rows,
        "themes": theme_rows,
        "setsTable": {
            "num": "\n".join(nums),
            "name": "\n".join(n.replace("\n", " ") for n in names),
            "year": b64("B", yrs),
            "theme": b64("H", tids),
            "off": b64("I", offs),
            "ci": b64("H", ci),
            "qty": b64("H", qty),
            "themeNames": theme_names,
        },
    }
    out = HERE / "payload.json"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    # a console summary for the verification table
    print(f"sets with parts: {len(per_set):,}; pieces: {sum(used.values()):,}; colours: {len(colours)}")
    print(f"themes charted: {len(theme_rows)}; payload {out.stat().st_size:,} bytes")
    for y in (1978, 2003, 2004, 2005, 2007, 2025):
        pc = year_pieces[y]; tot = sum(pc.values())
        share = lambda names: sum(v for k, v in pc.items() if raw_colours[k]["name"] in names) / tot * 100
        print(y, f"sets {year_sets[y]} pieces {tot:,} colours {len(pc)}",
              f"old grey {share(OLD_GREY):.1f}% new grey {share(NEW_GREY):.1f}%",
              f"brown {share({'Brown'}):.2f}% reddish brown {share({'Reddish Brown'}):.2f}%",
              f"classic {share(CLASSIC):.1f}%")


if __name__ == "__main__":
    main()
