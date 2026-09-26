CC     = gcc
IDIR   = include
CFLAGS = -Wall -Wextra -g -I$(IDIR)
LDLIBS = -lncurses
SRCDIR = src
OBJDIR = obj
BIN    = sudoku
PY     = .venv/bin/python
AUTO   = automation

SRCS = $(wildcard $(SRCDIR)/*.c)
OBJS = $(patsubst $(SRCDIR)/%.c,$(OBJDIR)/%.o,$(SRCS))

.PHONY: all build run clean test auto auto-scan auto-setup auto-test

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

auto-setup:
	python3 -m venv --system-site-packages .venv
	$(PY) -m pip install -q -r $(AUTO)/requirements.txt

auto: build
	cd $(AUTO) && ../$(PY) -m sudoku_auto

auto-scan: build
	cd $(AUTO) && ../$(PY) -m sudoku_auto --scan

auto-test: build
	cd $(AUTO) && ../$(PY) -m unittest -v
