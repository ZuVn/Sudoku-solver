#include <stdlib.h>
#include <time.h>

#include "generator.h"
#include "solver.h"

void generatorSeed(void)
{
    srand((unsigned int)time(NULL));
}

void generateFullSolution(Board *b)
{
    boardInit(b);
    solveBoardRandom(b);
}

void generatePuzzle(Board *b, int clues)
{
    int order[N * N];
    int i;
    int remaining = N * N;

    if (clues < 17)
    {
        clues = 17;
    }
    if (clues > N * N)
    {
        clues = N * N;
    }

    generateFullSolution(b);

    for (i = 0; i < N * N; i++)
    {
        order[i] = i;
    }

    for (i = N * N - 1; i > 0; i--)
    {
        int j = rand() % (i + 1);
        int tmp = order[i];

        order[i] = order[j];
        order[j] = tmp;
    }

    for (i = 0; i < N * N && remaining > clues; i++)
    {
        int r = order[i] / N;
        int c = order[i] % N;
        int saved = b->cells[r][c];

        b->cells[r][c] = 0;

        if (countSolutions(b, 2) == 1)
        {
            remaining--;
        }
        else
        {
            b->cells[r][c] = saved;
        }
    }

    computeCandidates(b);
}
