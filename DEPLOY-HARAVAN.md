# Triển khai để gắn Haravan

## Dữ liệu nhận và lưu ở đâu?

Máy chủ nhận và giao diện có thể dùng cùng một địa chỉ HTTPS. Không cần GitHub Pages để sử dụng ứng dụng. Repo GitHub lưu mã; service Render/VPS nhận dữ liệu. Không còn màn hình đăng nhập theo yêu cầu; endpoint báo cáo không xác thực. Nếu service công khai, người biết địa chỉ có thể xem báo cáo; muốn riêng tư cần giới hạn mạng/proxy.

## Render

1. Đăng nhập Render, kết nối repo private `phannohope98-png/do-dac` qua luồng GitHub chính thức.
2. Tạo Blueprint từ repo. `render.yaml` dựng Docker service và ổ lưu SQLite.
3. Điền `ANALYTICS_ORIGINS` bằng các origin Haravan thực tế, ví dụ `https://shopcuaban.vn,https://www.shopcuaban.vn`. Không có dấu `/` cuối; không nhập tên mẫu.
4. Kiểm tra chi phí trước khi tạo: cấu hình dùng service trả phí và persistent disk. Không dùng free filesystem cho dữ liệu thật vì dữ liệu mất khi service restart/redeploy; free service không gắn được disk.
5. Khi service Live, lấy URL Render cấp. Mở `/health` phải thấy `status: ok`. Mở URL gốc sẽ vào giao diện, tự kết nối bộ nhận cùng host. Không cần nhập URL/mật khẩu trên giao diện.

## Gắn Haravan sau khi máy chủ Live

Trong Haravan: Website → Giao diện → giao diện đang dùng → Chỉnh sửa code → Layouts → `theme.liquid`. Đặt trước `</body>`, thay `URL-SERVICE-THAT` bằng URL vừa được cấp:

```html
<script defer src="https://URL-SERVICE-THAT/tracker.js"></script>
```

Cùng đoạn đó gắn được nhiều web. Thêm origin của các web vào biến môi trường rồi redeploy service. Tên miền được nhận diện tự động.

Để ghi đúng đoạn nội dung thay vì phần trăm cuộn, đặt nhãn trên khối công khai:

```html
<section id="thong-so" data-analytics-section="Thông số hệ thống">...</section>
<section id="bao-gia" data-analytics-section="Bảng giá">...</section>
<section id="tu-van" data-analytics-section="Liên hệ tư vấn">...</section>
```

Nếu chưa gắn nhãn, mã dùng mốc h2/h3 trong main/article. Gắn một lần trên layout chung chỉ áp dụng các trang dùng layout đó; không khẳng định đo được checkout Haravan dùng layout riêng.

## Kiểm tra thật trước khi sử dụng

Mở website Haravan, đọc hai đoạn, bấm chuyển bài. Sau khoảng 5 giây, vào giao diện đo, chọn website. Phải có đúng trang và nhãn khu vực vừa xem. Tab Network phải thấy `/collect` trả 200. Không báo hoàn thành triển khai trước khi kiểm tra này qua.

## Nếu đã có VPS

Build `docker build -t do-dac .`, chạy container với ổ lưu `/var/data`, truyền `ANALYTICS_ORIGINS` rồi đặt reverse proxy HTTPS về cổng 8790. Giới hạn payload/tốc độ ở proxy, sao lưu SQLite định kỳ. Không mở báo cáo không xác thực cho người ngoài nếu muốn giữ riêng dữ liệu.

Repo này không có URL máy chủ đã triển khai. URL thật chỉ tồn tại sau khi tạo service trên tài khoản hosting bạn chọn.
