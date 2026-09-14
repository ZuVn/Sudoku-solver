#ifndef GENERATOR_H
#define GENERATOR_H

#include "board.h"

void generatorSeed(void);
void generateFullSolution(Board *b);
void generatePuzzle(Board *b, int clues);

#endif
