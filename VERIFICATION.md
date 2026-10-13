# Kiểm tra thực hiện

- 7 kiểm thử Python qua: báo cáo cần mã quản trị, origin không hợp lệ bị từ chối, chống trùng ID, loại query và trường không được phép, batch lỗi không ghi một phần, giới hạn batch, tệp SQLite không được phục vụ HTTP, timestamp lỗi bị từ chối.
- `node --check tracker.js` qua.
- Bản đầu đã thử trong trình duyệt localhost: chuỗi `/demo` → `/demo/article` → `/demo`, nút tư vấn, mục tiêu, mức cuộn 75%, Desktop và Chrome. Bản mới bỏ hộp hỏi và tự khởi động đo.
- `node test_tracker.cjs` kiểm tra tự khởi động không tạo banner, lượt xem, nút gọi không thu số điện thoại, mức cuộn, loại query, dừng/bật lại, tín hiệu GPC và chế độ điều khiển bên ngoài.
- Ảnh `web-analytics-preview.png` là báo cáo thao tác thử tại localhost, không phải lượt truy cập website công ty.
- Chưa cài lên website công ty. Chưa kiểm tra lưu lượng lớn, reverse proxy HTTPS thực tế, trình chặn theo dõi hoặc mọi trình duyệt di động.
