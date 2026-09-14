#include <stdlib.h>

#include "solver.h"

static void unitCell(int unit, int i, int *r, int *c)
{
    if (unit < N)
    {
        *r = unit;
        *c = i;
    }
    else if (unit < 2 * N)
    {
        *r = i;
        *c = unit - N;
    }
    else
    {
        int box = unit - 2 * N;

        *r = (box / BOX) * BOX + i / BOX;
        *c = (box % BOX) * BOX + i % BOX;
    }
}

static void placeDigit(Board *b, int r, int c, int d)
{
    int i, br, bc, rr, cc;
    int bit = bitOf(d);

    b->cells[r][c] = d;
    b->candidates[r][c] = 0;

    for (i = 0; i < N; i++)
    {
        b->candidates[r][i] &= ~bit;
        b->candidates[i][c] &= ~bit;
    }

    br = (r / BOX) * BOX;
    bc = (c / BOX) * BOX;

    for (rr = br; rr < br + BOX; rr++)
    {
        for (cc = bc; cc < bc + BOX; cc++)
        {
            b->candidates[rr][cc] &= ~bit;
        }
    }
}

void computeCandidates(Board *b)
{
    int r, c, i, br, bc, rr, cc;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] != 0)
            {
                b->candidates[r][c] = 0;
                continue;
            }

            b->candidates[r][c] = POSSIBLE;

            for (i = 0; i < N; i++)
            {
                if (b->cells[r][i] != 0)
                {
                    b->candidates[r][c] &= ~bitOf(b->cells[r][i]);
                }
                if (b->cells[i][c] != 0)
                {
                    b->candidates[r][c] &= ~bitOf(b->cells[i][c]);
                }
            }

            br = (r / BOX) * BOX;
            bc = (c / BOX) * BOX;

            for (rr = br; rr < br + BOX; rr++)
            {
                for (cc = bc; cc < bc + BOX; cc++)
                {
                    if (b->cells[rr][cc] != 0)
                    {
                        b->candidates[r][c] &= ~bitOf(b->cells[rr][cc]);
                    }
                }
            }
        }
    }
}

int propagate(Board *b)
{
    int changed = 1;

    while (changed)
    {
        int r, c, unit, d, i;

        changed = 0;

        for (r = 0; r < N; r++)
        {
            for (c = 0; c < N; c++)
            {
                if (b->cells[r][c] != 0)
                {
                    continue;
                }

                if (b->candidates[r][c] == 0)
                {
                    return 0;
                }

                if (popcount9(b->candidates[r][c]) == 1)
                {
                    placeDigit(b, r, c, lowestDigit(b->candidates[r][c]));
                    changed = 1;
                }
            }
        }

        for (unit = 0; unit < 3 * N; unit++)
        {
            for (d = 1; d <= N; d++)
            {
                int bit = bitOf(d);
                int seen = 0;
                int count = 0;
                int lastR = 0, lastC = 0;

                for (i = 0; i < N; i++)
                {
                    int ur, uc;

                    unitCell(unit, i, &ur, &uc);

                    if (b->cells[ur][uc] == d)
                    {
                        seen = 1;
                        break;
                    }

                    if (b->cells[ur][uc] == 0 && (b->candidates[ur][uc] & bit))
                    {
                        count++;
                        lastR = ur;
                        lastC = uc;
                    }
                }

                if (seen)
                {
                    continue;
                }

                if (count == 0)
                {
                    return 0;
                }

                if (count == 1)
                {
                    placeDigit(b, lastR, lastC, d);
                    changed = 1;
                }
            }
        }
    }

    return 1;
}

static int pickCell(const Board *b, int *bestR, int *bestC)
{
    int r, c, best = N + 1;
    int found = 0;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] == 0)
            {
                int n = popcount9(b->candidates[r][c]);

                if (n < best)
                {
                    best = n;
                    *bestR = r;
                    *bestC = c;
                    found = 1;
                }
            }
        }
    }

    return found;
}

static void shuffle(int *arr, int n)
{
    int i;

    for (i = n - 1; i > 0; i--)
    {
        int j = rand() % (i + 1);
        int tmp = arr[i];

        arr[i] = arr[j];
        arr[j] = tmp;
    }
}

/* Returns the number of solutions found, capped at `limit`.
   The first solution found is copied into `solution` when non-NULL. */
static int search(Board *b, int randomize, int limit, Board *solution)
{
    int r = 0, c = 0, i, n = 0;
    int order[N];

    if (!propagate(b))
    {
        return 0;
    }

    if (!pickCell(b, &r, &c))
    {
        if (solution != NULL)
        {
            boardCopy(solution, b);
        }
        return 1;
    }

    for (i = 0; i < N; i++)
    {
        order[i] = i + 1;
    }

    if (randomize)
    {
        shuffle(order, N);
    }

    for (i = 0; i < N; i++)
    {
        Board next;
        int found;

        if (!(b->candidates[r][c] & bitOf(order[i])))
        {
            continue;
        }

        boardCopy(&next, b);
        placeDigit(&next, r, c, order[i]);

        found = search(&next, randomize, limit - n, n == 0 ? solution : NULL);
        n += found;

        if (n >= limit)
        {
            break;
        }
    }

    return n;
}

static int solveWith(Board *b, int randomize)
{
    Board work;
    Board solution;

    boardCopy(&work, b);
    computeCandidates(&work);

    if (search(&work, randomize, 1, &solution) == 0)
    {
        return 0;
    }

    boardCopy(b, &solution);

    return 1;
}

int solveBoard(Board *b)
{
    return solveWith(b, 0);
}

int solveBoardRandom(Board *b)
{
    return solveWith(b, 1);
}

int countSolutions(const Board *b, int limit)
{
    Board work;

    boardCopy(&work, b);
    computeCandidates(&work);

    return search(&work, 0, limit, NULL);
}
