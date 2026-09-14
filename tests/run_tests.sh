#!/usr/bin/env bash
# Regression tests for ./sudoku. Run from the project root: make test
cd "$(dirname "$0")/.." || exit 1

BIN=./sudoku
pass=0
fail=0

ok()  { echo "PASS: $1"; pass=$((pass + 1)); }
bad() { echo "FAIL: $1"; fail=$((fail + 1)); }

# Print the 81 digits of the "Solution:" grid from solver output.
solution_digits() {
    sed -n '/^Solution:/,$p' | tail -n +2 | tr -cd '1-9.'
}

# Check a solved grid: 81 digits, every row/column/box holds 1-9.
grid_is_solved() {
    local g=$1 i j
    [ ${#g} -eq 81 ] || return 1
    for ((i = 0; i < 9; i++)); do
        local row="" col="" box=""
        for ((j = 0; j < 9; j++)); do
            row+=${g:i*9+j:1}
            col+=${g:j*9+i:1}
            box+=${g:((i/3*3 + j/3) * 9) + (i%3*3 + j%3):1}
        done
        for s in "$row" "$col" "$box"; do
            [ "$(echo "$s" | fold -w1 | sort | tr -d '\n')" = "123456789" ] || return 1
        done
    done
}

# Check that every clue in the puzzle is kept in the solution.
keeps_clues() {
    local p=$1 s=$2 i
    for ((i = 0; i < 81; i++)); do
        case ${p:i:1} in
            [1-9]) [ "${p:i:1}" = "${s:i:1}" ] || return 1 ;;
        esac
    done
}

puzzle_digits() {
    tr -cd '0-9.' < "$1" | tr '0' '.'
}

expect_solved() {
    local name=$1 file=$2 out sol
    out=$($BIN -f "$file" 2>&1) || { bad "$name (exit $?)"; return; }
    sol=$(echo "$out" | solution_digits)
    if grid_is_solved "$sol" && keeps_clues "$(puzzle_digits "$file")" "$sol"; then
        ok "$name"
    else
        bad "$name (wrong solution)"
    fi
}

expect_exit1() {
    local name=$1 file=$2
    $BIN -f "$file" >/dev/null 2>&1
    [ $? -eq 1 ] && ok "$name" || bad "$name (expected exit 1)"
}

expect_solved "easy"             tests/easy.txt
expect_solved "hard17"           tests/hard17.txt
expect_exit1  "invalid_duplicate" tests/invalid_duplicate.txt
expect_exit1  "unsolvable"       tests/unsolvable.txt

# stdin input
out=$($BIN -f - < tests/easy.txt 2>&1) && grid_is_solved "$(echo "$out" | solution_digits)" \
    && ok "stdin" || bad "stdin"

# generator round-trip
for i in 1 2 3; do
    tmp=$(mktemp)
    $BIN -g 28 | tail -n +2 > "$tmp"
    expect_solved "generate round-trip $i" "$tmp"
    rm -f "$tmp"
done

echo "----"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
