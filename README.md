# Sudoku Solver

Chương trình giải Sudoku 9×9 gồm hai phần:

- **Lõi C** (`./sudoku`): đọc đề, giải, sinh đề mới, và có giao diện ncurses trong terminal.
- **Tự động hóa Python** (`automation/`): tìm bảng Sudoku trên màn hình, đọc số, gọi `./sudoku` để giải,
  rồi dùng chuột và bàn phím ảo gõ đáp án vào các ô trống.

## Cách hoạt động

### Giải đề

1. Mỗi ô trống giữ một bitmask 9 bit ghi các số còn điền được.
2. Lan truyền ràng buộc: lặp lại *naked single* (ô chỉ còn một khả năng) và *hidden single*
   (một số chỉ đặt được vào một ô trong hàng, cột hoặc khối) cho tới khi không suy ra thêm được gì.
3. Nếu bảng chưa xong, chọn ô có ít khả năng nhất, thử từng số và quay lui khi gặp mâu thuẫn.
4. Sinh đề: tạo một bảng đầy đủ ngẫu nhiên, rồi xóa dần từng ô. Ô nào xóa đi làm đề có hơn một lời giải thì được trả lại.

### Tự động giải trên màn hình

1. Chụp toàn màn hình qua xdg-desktop-portal (chạy được trên GNOME Wayland và X11).
2. Tìm bảng 9×9 dựa vào 4 đường kẻ đậm chia khối 3×3, suy ra vị trí 10 đường dọc và 10 đường ngang.
3. Cắt 81 ô và nhận diện số bằng cách so khớp với mẫu chữ số vẽ từ font có sẵn trong máy. Không dùng OCR.
4. Gửi đề sang `./sudoku` để giải.
5. Qua `/dev/uinput`, click vào từng ô trống và gõ số. Ô có sẵn số thì không bị chạm tới.

Nếu có số đọc không chắc chắn, bảng đã đầy, hoặc đề không giải được, chương trình dừng và không gõ gì.

## Cài đặt

```bash
sudo apt install build-essential libncurses-dev python3-gi python3-tk python3-venv
make              # biên dịch ./sudoku
make auto-setup   # tạo .venv cho phần tự động hóa
```

Hãy đặt dự án trên phân vùng Linux (ext4). Biên dịch trên ổ NTFS (`/run/media/...`) có thể khiến `./sudoku` bị lỗi *Segmentation fault*.

## Chạy chương trình

| Lệnh | Tác dụng |
|---|---|
| `./sudoku` hoặc `make run` | Mở giao diện ncurses với bảng trống |
| `./sudoku -f <file>` | Giải đề trong file (`-f -` để đọc từ stdin) |
| `./sudoku -g [số_gợi_ý]` | Sinh đề có duy nhất một lời giải (mặc định 32 gợi ý) |
| `-i` (thêm sau `-f` hoặc `-g`) | Mở đề vừa đọc hoặc vừa sinh trong giao diện ncurses |
| `./sudoku -h` | Xem hướng dẫn nhanh |
| `make auto-scan` | Chụp màn hình, nhận diện và in lời giải, không gõ gì |
| `make auto` | Mở cửa sổ điều khiển tự động giải |
| `make test` / `make auto-test` | Chạy kiểm thử phần C / phần Python |

File đề gồm 81 ô đọc theo hàng. Chữ số `1`–`9` là ô có sẵn, ô trống ghi bằng `0`, `.`, `_` hoặc `*`. Các ký tự khác bị bỏ qua.

Mã thoát: `0` thành công, `1` đề sai hoặc không có lời giải, `2` tùy chọn không hợp lệ.

**Giao diện ncurses:** phím mũi tên (hoặc `h j k l`) để di chuyển, `1`–`9` để điền, `0`/`Space` để xóa ô,
`s` giải, `g` sinh đề mới, `c` xóa bảng, `q` thoát.

**Cửa sổ tự động (`make auto`):** mở đề sao cho thấy toàn bộ bảng, nhấn **Scan**, kiểm tra bản xem trước,
rồi nhấn **Fill**. Chương trình bắt đầu gõ sau 3 giây. Nút **Stop/Resume** và phím **F2** dùng chung một chức năng:
bấm lần đầu để dừng, bấm lần nữa để chụp lại màn hình và điền tiếp các ô còn trống. **Esc** chỉ dừng.
Khi đang điền, focus nằm ở trình duyệt, nên F2 chỉ dùng được nếu đã gán F2 trong Settings → Keyboard →
Custom Shortcuts cho lệnh `pkill -USR1 -f '^[^ ]*python[^ ]* -m sudoku_auto'`. Cần quyền ghi `/dev/uinput`, chỉ hỗ trợ một màn hình, và phím số hàng trên
phải gõ ra số mà không cần Shift.
