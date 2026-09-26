# Data Model

## `Board` (`include/board.h`)

```c
#define N 9          /* grid side */
#define BOX 3        /* box side */
#define POSSIBLE 0x1FF

typedef struct {
    int cells[N][N];       /* 0 = empty, 1..9 = digit */
    int candidates[N][N];  /* 9-bit mask of digits still allowed */
} Board;                   /* 648 bytes; copied by value in search */
```

- Coordinates are `(r, c)`, zero-based. Row-major index `i = r*9 + c`, used by the parser and the generator.
- Box index: `boxIndex(r, c) = (r/3)*3 + c/3` (0..8, row-major over boxes).
- `candidates` is only meaningful after `computeCandidates` (in `solver.c`). A filled cell always has mask `0`.
  `boardInit` sets every mask to `POSSIBLE`, which is not the same as "computed".

## Bitmask helpers

| Helper | Meaning |
|---|---|
| `bitOf(d)` | `1 << (d-1)`: digit 1 → bit 0, digit 9 → bit 8 |
| `popcount9(mask)` | Number of set bits (Kernighan loop). This is the cell's weight in MRV. |
| `lowestDigit(mask)` | Smallest digit whose bit is set, or 0 |

## Board API (`src/board.c`)

| Function | Returns | Notes |
|---|---|---|
| `boardInit(b)` | void | All cells 0, all masks `POSSIBLE` |
| `boardCopy(dst, src)` | void | `memcpy` of the whole struct |
| `boardCanPlace(b, r, c, v)` | 1/0 | Checks row, column and box, **skipping `(r,c)` itself**, so it also works to re-check a filled cell |
| `boardSetCell(b, r, c, v)` | 1/0 | Bounds check. `v=0` always allowed. Otherwise requires `boardCanPlace`. Does **not** update `candidates`. |
| `boardIsValid(b)` | 1/0 | No duplicate among the filled cells |
| `boardIsComplete(b)` | 1/0 | No zeros. Does not check validity. |
| `boardClueCount(b)` | int | Count of non-zero cells |
| `printPuzzle(b)` | void | stdout grid. The format is a contract, see [io_formats.md](io_formats.md). |

## Invariants

- The public API reports success as `int` 1 and failure as 0. There is no `bool` and no errno.
- The solver never trusts the incoming `candidates`. `solveWith` and `countSolutions` call
  `computeCandidates` on a copy first.
- Anything that writes `cells` directly (UI, generator) must call `computeCandidates` before relying on masks.
