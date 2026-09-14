#ifndef INPUT_H
#define INPUT_H

#include <stdio.h>

#include "board.h"

int parseBoardString(Board *b, const char *text);
int loadBoardFromStream(Board *b, FILE *fp);
int loadBoardFromFile(Board *b, const char *path);
int loadBoardFromStdin(Board *b);

#endif
