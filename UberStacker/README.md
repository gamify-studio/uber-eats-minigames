# UberStacker 🛍️

An Uber Eats–themed stacking game. Falling food — subs, combo meals, egg cartons + A2 milk, Asian takeout, grocery bags — drops into a paper bag. Pack it as tightly as you can: **rows don't clear**, so the whole skill is fitting the most food with the fewest gaps, all the way to the top.

Built as a branded game demo.

## Play

Open `index.html` in any browser, or visit the GitHub Pages URL once enabled.

## Controls

- **Desktop:** ← → move · ↑ rotate · ↓ soft drop · `space` hard drop · `P` pause
- **Mobile:** on-screen buttons (◀ ⟳ ▶ ⬇), tap the bag to rotate, swipe down to hard-drop

## Scoring

Score is **packing density** — `filled ÷ (width × stack height)`, normalized so a no-skill tower lands near **0%** and a solidly packed bag near **100%**. Completing a full row banks a "bag" (it stays on screen, it doesn't clear). A top-5 leaderboard is saved in `localStorage`.

## Pieces

Five food tetrominoes, each rendered from a hand-drawn pixel sprite:

| Shape | Food |
|---|---|
| I | Sub sandwiches |
| O | Uber Eats bag |
| L | Combo meal (drink + burger + fries) |
| S | Egg carton + A2 milk |
| T | Uber Groceries / takeout |

## Assets

`assets/slice.py` regenerates the transparent per-piece PNGs from the source sprite sheet (`assets/pieces-src.png`): it flood-fills the background to transparent, crops each piece, and quantizes it to a cell matrix. Requires Pillow + NumPy.

---

🤖 Built with [Claude Code](https://claude.com/claude-code)
