#include <stdlib.h>
#include <string.h>

#include "input.h"
#include "solver.h"

int parseBoardString(Board *b, const char *text)
{
    int count = 0;
    const char *p;

    boardInit(b);

    for (p = text; *p != '\0'; p++)
    {
        int value;

        if (*p >= '1' && *p <= '9')
        {
            value = *p - '0';
        }
        else if (*p == '0' || *p == '.' || *p == '_' || *p == '*')
        {
            value = 0;
        }
        else
        {
            continue;
        }

        if (count >= N * N)
        {
            fprintf(stderr, "Error: input has more than %d cells\n", N * N);
            return 0;
        }

        b->cells[count / N][count % N] = value;
        count++;
    }

    if (count != N * N)
    {
        fprintf(stderr, "Error: expected %d cells, got %d\n", N * N, count);
        return 0;
    }

    if (!boardIsValid(b))
    {
        fprintf(stderr, "Error: puzzle is invalid (duplicate digit in a row, column or box)\n");
        return 0;
    }

    computeCandidates(b);

    return 1;
}

int loadBoardFromStream(Board *b, FILE *fp)
{
    char buffer[4096];
    size_t len = 0;
    int ch;
    int ok;

    while ((ch = fgetc(fp)) != EOF && len < sizeof(buffer) - 1)
    {
        buffer[len++] = (char)ch;
    }
    buffer[len] = '\0';

    ok = parseBoardString(b, buffer);

    return ok;
}

int loadBoardFromFile(Board *b, const char *path)
{
    FILE *fp = fopen(path, "r");
    int ok;

    if (fp == NULL)
    {
        fprintf(stderr, "Error: cannot open '%s'\n", path);
        return 0;
    }

    ok = loadBoardFromStream(b, fp);
    fclose(fp);

    return ok;
}

int loadBoardFromStdin(Board *b)
{
    return loadBoardFromStream(b, stdin);
}
