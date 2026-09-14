#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "board.h"
#include "solver.h"
#include "input.h"
#include "generator.h"
#include "ui.h"

static void usage(const char *prog)
{
    printf("Usage: %s [options]\n", prog);
    printf("  (no options)        interactive ncurses editor with an empty board\n");
    printf("  -f <file>           load a puzzle from a file ('-' for stdin) and solve it\n");
    printf("  -g [clues]          generate a random puzzle (default 32 clues)\n");
    printf("  -i                  open the interactive editor with the loaded/generated board\n");
    printf("  -h                  show this help\n");
    printf("\nPuzzle format: 81 cells, digits 1-9, '0' or '.' for empty.\n");
    printf("Whitespace and separator characters are ignored.\n");
}

int main(int argc, char **argv)
{
    Board board;
    const char *path = NULL;
    int interactive = 0;
    int generate = 0;
    int clues = 32;
    int i;

    boardInit(&board);

    for (i = 1; i < argc; i++)
    {
        if (strcmp(argv[i], "-f") == 0 && i + 1 < argc)
        {
            path = argv[++i];
        }
        else if (strcmp(argv[i], "-i") == 0)
        {
            interactive = 1;
        }
        else if (strcmp(argv[i], "-g") == 0)
        {
            generate = 1;

            if (i + 1 < argc && argv[i + 1][0] != '-')
            {
                clues = atoi(argv[++i]);
            }
        }
        else if (strcmp(argv[i], "-h") == 0)
        {
            usage(argv[0]);
            return 0;
        }
        else
        {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            usage(argv[0]);
            return 2;
        }
    }

    generatorSeed();

    if (path != NULL)
    {
        int ok = (strcmp(path, "-") == 0)
                     ? loadBoardFromStdin(&board)
                     : loadBoardFromFile(&board, path);

        if (!ok)
        {
            return 1;
        }
    }
    else if (generate)
    {
        generatePuzzle(&board, clues);
    }
    else
    {
        interactive = 1;
    }

    if (interactive)
    {
        runInteractiveUI(&board);
        return 0;
    }

    if (generate)
    {
        printf("Generated puzzle (%d clues):\n", boardClueCount(&board));
        printPuzzle(&board);
        return 0;
    }

    printf("Puzzle:\n");
    printPuzzle(&board);

    if (!solveBoard(&board))
    {
        fprintf(stderr, "No solution.\n");
        return 1;
    }

    printf("Solution:\n");
    printPuzzle(&board);

    return 0;
}
