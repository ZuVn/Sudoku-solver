# Sudoku Solver

Chương trình giải Sudoku 9×9 viết bằng C. Có ba cách dùng:

- **Giải đề từ file hoặc stdin**, in kết quả ra màn hình.
- **Sinh đề ngẫu nhiên** có duy nhất một lời giải.
- **Giao diện tương tác** (ncurses): nhập đề bằng bàn phím rồi giải ngay trong terminal.

## 1. Cài đặt

Cần `gcc`, `make` và thư viện ncurses.

```bash
# Ubuntu / Debian
sudo apt install build-essential libncurses-dev

# Fedora
sudo dnf install gcc make ncurses-devel
```

## 2. Biên dịch

```bash
make          # biên dịch, tạo file chạy ./sudoku
make run      # biên dịch rồi mở giao diện tương tác
make test     # chạy bộ kiểm thử
make clean    # xóa obj/ và ./sudoku
```

> **Lưu ý:** Hãy đặt dự án trên phân vùng Linux (ext4…). Nếu đặt trên ổ NTFS gắn ngoài
> (ví dụ `/run/media/...`), file `./sudoku` có thể bị *Segmentation fault* ngay khi chạy,
> dù mã nguồn không có lỗi.

## 3. Các tùy chọn dòng lệnh

| Lệnh | Tác dụng |
|---|---|
| `./sudoku` | Mở giao diện tương tác với bảng trống |
| `./sudoku -f <file>` | Đọc đề từ file, giải và in kết quả |
| `./sudoku -f -` | Đọc đề từ stdin |
| `./sudoku -g [số_gợi_ý]` | Sinh đề ngẫu nhiên (mặc định 32 ô gợi ý) |
| `./sudoku -f <file> -i` | Đọc đề từ file rồi mở trong giao diện tương tác |
| `./sudoku -g [số_gợi_ý] -i` | Sinh đề rồi mở trong giao diện tương tác |
| `./sudoku -h` | Xem hướng dẫn nhanh |

### Mã thoát

| Mã | Ý nghĩa |
|---|---|
| `0` | Thành công |
| `1` | Đề sai định dạng, có số trùng, hoặc không có lời giải |
| `2` | Tùy chọn không hợp lệ |

## 4. Định dạng file đề

- Đề gồm đúng **81 ô**, đọc từ trái sang phải, từ trên xuống dưới.
- Chữ số `1`–`9` là ô đã có số.
- Ô trống ghi bằng `0`, `.`, `_` hoặc `*`.
- Mọi ký tự khác (dấu cách, xuống dòng, `|`, `-`…) đều bị bỏ qua, nên có thể trình bày tùy ý.

Ba cách viết dưới đây là cùng một đề:

```text
53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79
```

```text
53. .7. ...
6.. 195 ...
.98 ... .6.

8.. .6. ..3
4.. 8.3 ..1
7.. .2. ..6

.6. ... 28.
... 419 ..5
... .8. .79
```

```text
530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079
```

## 5. Ví dụ sử dụng

### Giải đề từ file

```bash
./sudoku -f tests/easy.txt
```

```text
Puzzle:
-------------------------------
| 5  3  . | .  7  . | .  .  . |
| 6  .  . | 1  9  5 | .  .  . |
...
Solution:
-------------------------------
| 5  3  4 | 6  7  8 | 9  1  2 |
| 6  7  2 | 1  9  5 | 3  4  8 |
...
```

### Nhập đề trực tiếp qua stdin

```bash
echo "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79" | ./sudoku -f -
```

### Sinh đề rồi giải luôn

Dòng đầu tiên của `-g` là tiêu đề, nên bỏ dòng đó bằng `tail -n +2` trước khi đưa sang `-f -`:

```bash
./sudoku -g 28 | tail -n +2 | ./sudoku -f -
```

### Lưu đề sinh ra vào file

```bash
./sudoku -g 30 | tail -n +2 > de_moi.txt
./sudoku -f de_moi.txt
```

### Về số ô gợi ý khi sinh đề

- Giá trị hợp lệ từ **17 đến 81**. Nhỏ hơn 17 được tính là 17, lớn hơn 81 được tính là 81.
- Đề sinh ra luôn có **duy nhất một lời giải**. Nếu xóa thêm ô sẽ làm đề có nhiều lời giải,
  chương trình dừng lại. Vì vậy số gợi ý thực tế có thể **nhiều hơn** số bạn yêu cầu
  (ví dụ `-g 17` thường cho đề khoảng 22–26 gợi ý). Tiêu đề in ra luôn ghi số thực tế.
- Ít gợi ý hơn thường là đề khó hơn: khoảng 40–50 là dễ, khoảng 25–32 là khó.

## 6. Giao diện tương tác

Mở bằng `./sudoku`, `make run`, hoặc thêm `-i` vào lệnh `-f` / `-g`.

### Phím điều khiển

| Phím | Tác dụng |
|---|---|
| `←` `↑` `↓` `→` hoặc `h` `k` `j` `l` | Di chuyển con trỏ |
| `1`–`9` | Điền số vào ô đang chọn |
| `0`, `Space`, `Backspace` | Xóa ô đang chọn |
| `s` | Giải bảng hiện tại |
| `g` | Sinh đề mới (32 gợi ý), thay thế bảng hiện tại |
| `c` | Xóa trắng toàn bộ bảng |
| `q` | Thoát |

### Cách dùng

1. Di chuyển tới ô cần điền rồi gõ số. Số đã điền hiển thị **in đậm**, ô trống hiển thị `.`.
2. Nếu số vừa gõ trùng với hàng, cột hoặc khối 3×3, chương trình báo
   `That digit conflicts with its row, column or box.` và không điền số đó.
   Nhấn phím bất kỳ để tiếp tục.
3. Nhập xong đề thì nhấn `s`:
   - Có lời giải: bảng được điền đầy đủ và hiện `Solved.`
   - Không có lời giải: bảng giữ nguyên và hiện `No solution for this board.`

   Nhấn phím bất kỳ để quay lại chỉnh sửa.
4. Nhấn `q` để thoát. Terminal sẽ trở lại bình thường.

## 7. Tự động giải Sudoku trên màn hình

Công cụ chụp màn hình, tìm bảng 9×9 (ví dụ đang mở trên Chrome), đọc các số, giải bằng `./sudoku`,
rồi tự di chuyển chuột và gõ số vào các ô trống. Chạy được trên GNOME Wayland (và X11).

```bash
sudo apt install python3-gi python3-tk python3-venv
make auto-setup   # tạo .venv và cài numpy, pillow
make auto-scan    # chỉ chụp, nhận diện và in lời giải, không gõ gì
make auto         # mở cửa sổ điều khiển
```

Cách dùng cửa sổ: mở đề trên Chrome sao cho thấy toàn bộ bảng, nhấn **Scan** và kiểm tra bảng xem trước,
rồi nhấn **Fill**. Sau 3 giây chương trình bắt đầu gõ. Chỉ các ô trống mới được điền.

- Dừng: nút **Stop**, phím **Esc** (khi cửa sổ đang được chọn), hoặc chạy `pkill -USR1 -f sudoku_auto`.
  Có thể gán lệnh này cho một phím tắt trong GNOME Settings → Keyboard → Custom Shortcuts.
- Cần quyền ghi `/dev/uinput`, chỉ hỗ trợ một màn hình, và bàn phím phải gõ được số ở hàng phím số mà không cần Shift.
- Nếu đọc sai số hoặc đề không giải được, chương trình không gõ gì và báo lỗi.

## 8. Kiểm thử

```bash
make test
```

Script [tests/run_tests.sh](tests/run_tests.sh) kiểm tra các trường hợp sau:

| File / kiểm tra | Mong đợi |
|---|---|
| `tests/easy.txt` | Giải đúng |
| `tests/hard17.txt` | Giải đúng (đề 17 gợi ý, rất khó) |
| `tests/invalid_duplicate.txt` | Báo lỗi số trùng, mã thoát 1 |
| `tests/unsolvable.txt` | Báo `No solution.`, mã thoát 1 |
| Đọc từ stdin | Giải đúng |
| Sinh đề 3 lần rồi giải lại | Cả 3 đều giải được |

Một lời giải được tính là đúng khi mỗi hàng, cột và khối 3×3 có đủ các số 1–9, và mọi ô gợi ý
của đề được giữ nguyên. Giao diện ncurses không kiểm thử tự động được, cần thử bằng tay.

Phần tự động hóa: `make auto-test` (17 kiểm thử, gồm ảnh chụp thật từ websudoku và sudoku-online).

## 9. Cấu trúc dự án

```text
include/          header của các module
src/
  sudoku.c        hàm main, xử lý tùy chọn dòng lệnh
  board.c         kiểu Board, kiểm tra hợp lệ, in bảng
  input.c         đọc đề từ chuỗi, file, stdin
  solver.c        thuật toán giải và đếm số lời giải
  generator.c     sinh đề ngẫu nhiên có lời giải duy nhất
  ui.c            giao diện ncurses
tests/            file đề mẫu và run_tests.sh
automation/
  sudoku_auto/    chụp màn hình, nhận diện bảng và số, chuột/bàn phím ảo, cửa sổ Tk
  tests/          kiểm thử Python và ảnh mẫu
makefile
```

### Thuật toán giải

1. **Lan truyền ràng buộc:** mỗi ô trống có một bitmask 9 bit ghi các số còn điền được.
   Chương trình lặp lại hai luật cho tới khi không suy ra thêm được gì:
   - *Naked single:* ô chỉ còn một khả năng thì điền số đó.
   - *Hidden single:* một số chỉ đặt được vào đúng một ô trong hàng, cột hoặc khối thì điền vào ô đó.
2. **Quay lui (backtracking):** nếu bảng vẫn chưa xong, chọn ô có **ít khả năng nhất** (MRV),
   thử lần lượt từng số, lan truyền lại, và quay lui khi gặp mâu thuẫn.
3. **Sinh đề:** tạo một lời giải đầy đủ bằng quay lui với thứ tự số ngẫu nhiên. Sau đó xóa dần
   từng ô theo thứ tự ngẫu nhiên. Mỗi lần xóa, kiểm tra xem đề còn đúng một lời giải không
   (`countSolutions` với giới hạn 2); nếu không thì trả lại ô đó.
