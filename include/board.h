#ifndef BOARD_H
#define BOARD_H

#define N 9
#define BOX 3
#define POSSIBLE 0x1FF

typedef struct {
    int cells[N][N];
    int candidates[N][N];
} Board;

static inline int boxIndex(int r, int c)
{
    return (r / BOX) * BOX + (c / BOX);
}

static inline int bitOf(int digit)
{
    return 1 << (digit - 1);
}

int popcount9(int mask);
int lowestDigit(int mask);

void boardInit(Board *b);
void boardCopy(Board *dst, const Board *src);
int boardCanPlace(const Board *b, int r, int c, int val);
int boardSetCell(Board *b, int r, int c, int val);
int boardIsValid(const Board *b);
int boardIsComplete(const Board *b);
int boardClueCount(const Board *b);
void printPuzzle(const Board *b);

#endif
