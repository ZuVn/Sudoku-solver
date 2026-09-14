#ifndef SOLVER_H
#define SOLVER_H

#include "board.h"

void computeCandidates(Board *b);
int propagate(Board *b);
int solveBoard(Board *b);
int solveBoardRandom(Board *b);
int countSolutions(const Board *b, int limit);

#endif
