#include <ncurses.h>
#include <string.h>

#include "ui.h"
#include "solver.h"
#include "generator.h"

#define GRID_TOP 0
#define STATUS_ROW 14
#define MESSAGE_ROW 15

static int screenRow(int r)
{
    return GRID_TOP + 1 + r + (r / BOX);
}

static int screenCol(int c)
{
    return c * 3 + (c / BOX) + 2;
}

static void markFixed(const Board *b, int fixed[N][N])
{
    int r, c;

    for (r = 0; r < N; r++)
    {
        for (c = 0; c < N; c++)
        {
            fixed[r][c] = (b->cells[r][c] != 0);
        }
    }
}

static void drawGrid(const Board *b, int fixed[N][N])
{
    int r, c;
    int line = GRID_TOP;

    mvprintw(line++, 0, "-------------------------------");

    for (r = 0; r < N; r++)
    {
        mvprintw(line, 0, "|");

        for (c = 0; c < N; c++)
        {
            int col = screenCol(c);

            if (b->cells[r][c] == 0)
            {
                mvaddch(line, col, '.');
            }
            else
            {
                if (fixed[r][c])
                {
                    attron(A_BOLD);
                }
                mvaddch(line, col, '0' + b->cells[r][c]);
                if (fixed[r][c])
                {
                    attroff(A_BOLD);
                }
            }

            if (((c + 1) % BOX) == 0)
            {
                mvaddch(line, col + 2, '|');
            }
        }

        line++;

        if (((r + 1) % BOX) == 0)
        {
            mvprintw(line++, 0, "-------------------------------");
        }
    }

    mvprintw(STATUS_ROW, 0,
             "arrows/hjkl: move  1-9: enter  0/space: clear cell");
    mvprintw(STATUS_ROW + 1, 0,
             "s: solve  g: generate  c: clear board  q: quit");
}

static void showMessage(const char *msg)
{
    move(MESSAGE_ROW + 1, 0);
    clrtoeol();
    mvprintw(MESSAGE_ROW + 1, 0, "%s", msg);
}

void runInteractiveUI(Board *b)
{
    int fixed[N][N];
    int curR = 0, curC = 0;
    int running = 1;

    markFixed(b, fixed);

    initscr();
    noecho();
    cbreak();
    keypad(stdscr, TRUE);
    curs_set(1);

    while (running)
    {
        int ch;

        erase();
        drawGrid(b, fixed);
        move(screenRow(curR), screenCol(curC));
        refresh();

        ch = getch();

        switch (ch)
        {
        case KEY_UP:
        case 'k':
            if (curR > 0) curR--;
            break;

        case KEY_DOWN:
        case 'j':
            if (curR < N - 1) curR++;
            break;

        case KEY_LEFT:
        case 'h':
            if (curC > 0) curC--;
            break;

        case KEY_RIGHT:
        case 'l':
            if (curC < N - 1) curC++;
            break;

        case '0':
        case ' ':
        case KEY_BACKSPACE:
        case 127:
            b->cells[curR][curC] = 0;
            fixed[curR][curC] = 0;
            break;

        case 's':
        {
            Board work;

            boardCopy(&work, b);

            if (solveBoard(&work))
            {
                boardCopy(b, &work);
                erase();
                drawGrid(b, fixed);
                showMessage("Solved.");
            }
            else
            {
                erase();
                drawGrid(b, fixed);
                showMessage("No solution for this board.");
            }

            move(screenRow(curR), screenCol(curC));
            refresh();
            getch();
            break;
        }

        case 'g':
            generatePuzzle(b, 32);
            markFixed(b, fixed);
            break;

        case 'c':
            boardInit(b);
            markFixed(b, fixed);
            break;

        case 'q':
            running = 0;
            break;

        default:
            if (ch >= '1' && ch <= '9')
            {
                if (!boardSetCell(b, curR, curC, ch - '0'))
                {
                    erase();
                    drawGrid(b, fixed);
                    showMessage("That digit conflicts with its row, column or box.");
                    move(screenRow(curR), screenCol(curC));
                    refresh();
                    getch();
                }
                else
                {
                    fixed[curR][curC] = 1;
                }
            }
            break;
        }
    }

    endwin();
}
