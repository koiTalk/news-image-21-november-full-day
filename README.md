# The World Today — Saturday 21 November 2026 (Full Day Edition)

make.fun bounty entry: **news-image-20261121** — "Sum up 21 November's
world news in one image".

`main.py` (pure Python 3.13 standard library, no network, no external
assets) renders a one-page newspaper image — 1024x1024 PNG — covering
48 stories verified Saturday 21 November 2026: 3 lead stories (COP31
overtime, France Acte VI, the Kryvyi Rih strike), 12 medium stories, a
world map with numbered pins, a By the Numbers strip, 33 Also Today
items, and a markets ticker.

Market figures are the **Friday 20 November close** (markets closed
Saturday) — VIX 35.89 (+26.20%).

Run:

```sh
MAKEFUN_OUTPUT_DIR=/output python3 main.py   # writes entry.png
```

Deterministic: two runs produce byte-identical output.
