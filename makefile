CC     = gcc
IDIR   = include
CFLAGS = -Wall -Wextra -g -I$(IDIR)
LDLIBS = -lncurses
SRCDIR = src
OBJDIR = obj
BIN    = sudoku

SRCS = $(wildcard $(SRCDIR)/*.c)
OBJS = $(patsubst $(SRCDIR)/%.c,$(OBJDIR)/%.o,$(SRCS))

.PHONY: all build run clean test

all: build

build: $(BIN)

$(BIN): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(OBJDIR):
	mkdir -p $(OBJDIR)

run: build
	./$(BIN)

clean:
	rm -rf $(OBJDIR) $(BIN)

test: build
	./tests/run_tests.sh
