# Uber Eats Merge — food renders

Drop your 6 food images here. The game wires each level to a file by number:

| Level | File     | Item            |
|-------|----------|-----------------|
| 1     | `1.png`  | Burger          |
| 2     | `2.png`  | Coffee          |
| 3     | `3.png`  | Noodles         |
| 4     | `4.png`  | Smoothie        |
| 5     | `5.png`  | Groceries       |
| 6     | `6.png`  | Uber Eats Bag (win) |

Notes:
- **Transparent PNG**, no baked numbers. The game draws the level number (bottom-right) itself
  while `CONFIG.numbersInImage` is `false`, so numbers are a uniform size on every tile.
- Square-ish renders, ~400px+, similar visual weight.
- Square-ish renders, ~400×400px+, all roughly the same visual weight.
- Until a file exists, the game shows an emoji fallback for that level — so it stays playable.
- Filenames/paths are configurable in `10ten.html` → `CONFIG.itemImg` / `CONFIG.items`.
