# Solver Algorithm (`src/solver.c`, `src/generator.c`)

## 1. Candidate computation, `computeCandidates(b)`

For each empty cell: start from `POSSIBLE`, then clear the bits of the digits already in its row, column and box.
Filled cells get mask 0. Cost: O(81·27).

## 2. Placement, `placeDigit(b, r, c, d)` (static)

Sets `cells[r][c] = d` and `candidates[r][c] = 0`, and clears `bitOf(d)` from every peer in the row,
column and box. This is the only way the solver fills cells.

## 3. Propagation, `propagate(b)`

Repeats until a full pass changes nothing:

1. **Naked single:** for each empty cell, mask `0` means contradiction (return 0). If `popcount9 == 1`,
   place that digit.
2. **Hidden single:** for each of the 27 units (`unitCell` maps unit 0–8 to rows, 9–17 to columns,
   18–26 to boxes) and each digit 1–9, skip the digit if it is already placed in the unit. Otherwise count the
   empty cells whose mask allows it. Count 0 means contradiction (return 0). Count 1 means place it.

Returns 1 when stable with no contradiction. The board may still have empty cells.

## 4. Weight calculation and cell choice, `pickCell` (static)

- **Weight of an empty cell = `popcount9(candidates[r][c])`**, the number of legal digits (1..9).
- It picks the empty cell with the **minimum weight** (Minimum Remaining Values). The strict `<` comparison
  means ties go to the first cell in row-major order.
- A weight of 0 cannot reach here, because `propagate` already rejected it.
- Returns 0 when there is no empty cell, meaning the board is solved.

This is the only heuristic weighting in the codebase. There is no digit ordering heuristic (LCV):
digits are tried 1..9, or shuffled when `randomize=1`.

## 5. Search, `search(b, randomize, limit, solution)` (static, recursive)

```
if !propagate(b): return 0
if !pickCell(b): copy b to solution (if non-NULL); return 1
for each digit d in order (1..9 or shuffled) allowed at (r,c):
    next = copy of b; placeDigit(next, r, c, d)
    n += search(next, randomize, limit - n, n == 0 ? solution : NULL)
    if n >= limit: break
return n
```

- The recursion depth is at most the number of empty cells (≤ 81), and each frame holds one `Board` (648 B).
  Stack use is small.
- `solution` receives only the **first** solution found.

## 6. Public entry points

| Function | Behavior |
|---|---|
| `solveBoard(b)` | Copy, compute candidates, search with limit 1, deterministic. On success writes the solution into `b` and returns 1. On failure `b` is **unchanged** and it returns 0. |
| `solveBoardRandom(b)` | Same, but with shuffled digit order. Used to build random full grids. |
| `countSolutions(b, limit)` | Number of solutions, capped at `limit`. `b` is const. `limit=2` is the uniqueness test. |

## 7. Generator (`src/generator.c`)

1. `generatorSeed()`: `srand(time(NULL))`. Two runs in the same second give the same puzzle.
2. `generateFullSolution`: `boardInit` + `solveBoardRandom` on an empty board.
3. `generatePuzzle(b, clues)`: clamp `clues` to [17, 81]. Shuffle the 81 indices (Fisher–Yates with `rand()`).
   For each index, while `remaining > clues`: blank the cell. If `countSolutions(b, 2) != 1`, restore it.
   Finally call `computeCandidates`.
   - Each index is tried once, so the result can have more clues than requested.
   - Uniqueness is guaranteed.

## Performance notes

- `hard17.txt` (17 clues) solves instantly thanks to propagation + MRV.
- Generation cost is dominated by up to 81 `countSolutions(…, 2)` calls. Low clue targets are slower.
- If you optimize, keep the observable behavior the same: first solution in 1..9 digit order for
  `solveBoard`, and the `solveBoard` failure contract.
