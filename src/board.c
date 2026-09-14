#include <stdio.h>
#include <string.h>

#include "board.h"

int popcount9(int mask)
{
    int count = 0;

    while (mask)
    {
        mask &= mask - 1;
        count++;
    }

    return count;
}

int lowestDigit(int mask)
{
    int d;

    for (d = 1; d <= N; d++)
    {
        if (mask & bitOf(d))
        {
            return d;
        }
    }

    return 0;
}

void boardInit(Board *b)
{
    int r, c;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            b->cells[r][c] = 0;
            b->candidates[r][c] = POSSIBLE;
        }
    }
}

void boardCopy(Board *dst, const Board *src)
{
    memcpy(dst, src, sizeof(Board));
}

int boardCanPlace(const Board *b, int r, int c, int val)
{
    int i, br, bc, rr, cc;

    for (i = 0; i < N; i++)
    {
        if (i != c && b->cells[r][i] == val)
        {
            return 0;
        }
        if (i != r && b->cells[i][c] == val)
        {
            return 0;
        }
    }

    br = (r / BOX) * BOX;
    bc = (c / BOX) * BOX;

    for (rr = br; rr < br + BOX; rr++)
    {
        for (cc = bc; cc < bc + BOX; cc++)
        {
            if ((rr != r || cc != c) && b->cells[rr][cc] == val)
            {
                return 0;
            }
        }
    }

    return 1;
}

int boardSetCell(Board *b, int r, int c, int val)
{
    if (r < 0 || r >= N || c < 0 || c >= N || val < 0 || val > N)
    {
        return 0;
    }

    if (val != 0 && !boardCanPlace(b, r, c, val))
    {
        return 0;
    }

    b->cells[r][c] = val;

    return 1;
}

int boardIsValid(const Board *b)
{
    int r, c;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] != 0 && !boardCanPlace(b, r, c, b->cells[r][c]))
            {
                return 0;
            }
        }
    }

    return 1;
}

int boardIsComplete(const Board *b)
{
    int r, c;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] == 0)
            {
                return 0;
            }
        }
    }

    return 1;
}

int boardClueCount(const Board *b)
{
    int r, c, count = 0;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] != 0)
            {
                count++;
            }
        }
    }

    return count;
}

void printPuzzle(const Board *b)
{
    int r, c;

    printf("-------------------------------\n");
    for (r = 0; r < N; r++)
    {
        printf("|");
        for (c = 0; c < N; c++)
        {
            if (b->cells[r][c] == 0)
            {
                printf(" . ");
            }
            else
            {
                printf(" %d ", b->cells[r][c]);
            }

            if (((c + 1) % BOX) == 0)
            {
                printf("|");
            }
        }
        printf("\n");
        if (((r + 1) % BOX) == 0)
        {
            printf("-------------------------------\n");
        }
    }
}
