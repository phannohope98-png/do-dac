# Solar Journey — đo hành trình truy cập website

Bộ mã tự lưu dữ liệu: `tracker.js` gắn vào website; `server.py` nhận dữ liệu vào SQLite; `dashboard.html` xem biểu đồ và hành trình. Không có tài khoản/mật khẩu website của bạn trong bộ mã.

## Đo được gì?

- Phiên ẩn danh, thiết bị Mobile/Desktop, nhóm trình duyệt.
- Trang đã xem và thứ tự chuyển trang; nguồn giới thiệu hoặc UTM source/medium/campaign.
- Link/nút đã nhấp, form đã gửi (không lấy nội dung), mục tiêu đánh dấu.
- Mốc cuộn 25/50/75/100%, thời gian trang hiện và có hoạt động gần đây.
- Trang cuối quan sát được, biểu đồ lượt xem, nguồn và hành trình từng phiên.

**Không biết danh tính khách**, không đếm chính xác số người: một người có thể có nhiều phiên. Không ghi IP, nội dung nhập, mật khẩu, ảnh màn hình hay fingerprint. Thời gian hoạt động không chứng minh khách đã đọc. Chuyển tab không chứng minh khách thoát. Trình chặn, mạng lỗi hoặc tín hiệu DNT/GPC khiến số liệu thiếu. Dữ liệu trình duyệt gửi có thể bị giả; đây không phải hệ thống phát hiện bot hoặc chứng minh người thật.

Google thường không chuyển từ khóa organic vào referrer. Dùng Google Search Console để xem từ khóa ở mức tổng hợp; không gán từ khóa đó cho từng khách. Bộ mã này không đo từ khóa tìm kiếm nội bộ mặc định vì khách có thể nhập dữ liệu cá nhân. UTM phải là nhãn chiến dịch, không chứa email/số điện thoại.

## Chạy thử trên máy của bạn

Cần Python 3.11 trở lên; không cần cài thư viện ngoài.

```powershell
cd duong-dan-den-web-analytics
python server.py
```

Máy chủ in địa chỉ `http://127.0.0.1:8790` và **mã quản trị riêng**. Mở địa chỉ đó, nhập mã. Mở `http://127.0.0.1:8790/demo`, cuộn và chuyển bài, bấm nút tư vấn. Quay về báo cáo, bấm Làm mới. Dữ liệu thử thực sự được tracker gửi và lưu; không phải số liệu dựng sẵn.

Kiểm thử: `python -m unittest test_server.py`. Dữ liệu thử nghiệm nằm trong `private-data/analytics.sqlite`; không chia sẻ thư mục này công khai.

## Cài trên website thật

**Không thể chỉ dán JavaScript rồi tự có báo cáo.** Bạn cần chạy bộ nhận trên máy chủ Python/VPS luôn hoạt động, đặt sau reverse proxy HTTPS. Gói này chưa phải tệp PHP để chép vào DirectAdmin. Website PHP vẫn gắn được JavaScript, nhưng hosting chỉ hỗ trợ PHP cần một máy chủ nhận riêng hoặc chuyển backend sang PHP trước khi cài.

1. Đặt bộ nhận trên máy chủ, tạo mã quản trị dài ngẫu nhiên và cấu hình biến môi trường. Ví dụ Linux:

```sh
export ANALYTICS_SITE=thesun
export ANALYTICS_ORIGINS=https://thesunvn.com.vn,https://www.thesunvn.com.vn
export ANALYTICS_ADMIN_TOKEN='THAY_BANG_MA_NGAU_NHIEN_DAI_CUA_BAN'
export ANALYTICS_DB=/var/lib/solar-journey/analytics.sqlite
python3 server.py
```

2. Reverse proxy tên miền HTTPS, ví dụ `https://analytics.tenmiencuaban.vn`, về `127.0.0.1:8790`; chạy bằng service tự khởi động. Giữ cổng 8790 nội bộ. Đặt giới hạn request/tốc độ ở proxy; origin allowlist không ngăn người khác giả mạo request. Mã quản trị chỉ nhập ở trang báo cáo, **không chèn vào website/JavaScript**. Sao lưu SQLite bằng công cụ SQLite backup; không chỉ copy tệp đang ghi.
3. Chép `tracker.js` lên website, rồi đặt đoạn sau trước `</body>` trong layout dùng chung. Thay URL máy chủ nhận:

```html
<script defer src="/assets/tracker.js"
  data-site="thesun"
  data-endpoint="https://analytics.tenmiencuaban.vn/collect"></script>
```

4. Đánh dấu nút bằng nhãn cố định để báo cáo dễ hiểu:

```html
<a href="https://zalo.me/DUONG_DAN_CUA_BAN"
   data-analytics="Chat Zalo" data-analytics-goal="Mở Zalo">Chat Zalo</a>
<a href="/bai-viet/ve-sinh-tam-pin" data-analytics="Bài vệ sinh tấm pin">Đọc bài</a>
<form data-analytics="Yêu cầu khảo sát">...</form>
<button onclick="SolarAnalytics.stop()">Tắt đo truy cập</button>
```

Mục tiêu bấm nút chỉ chứng minh nút được bấm. Để đo form được backend chấp nhận, gọi `SolarAnalytics.track('Yêu cầu đã gửi thành công')` **sau phản hồi thành công**, không gọi ngay khi bấm gửi. Không truyền tên, email, điện thoại hoặc nội dung form vào tên sự kiện.

Tracker mặc định tự chạy, không hiện hộp hỏi, không cần quyền truy cập thiết bị. Phiên ẩn danh dùng sessionStorage, hết hạn sau 30 phút không có sự kiện. Không dùng localStorage để lưu lựa chọn đồng ý. Tín hiệu DNT/GPC vẫn chặn theo dõi. `SolarAnalytics.stop()` dừng và ghi nhớ tắt trong phiên tab; `SolarAnalytics.start()` bật lại.

Nếu website muốn chủ động điều khiển lúc bắt đầu, thêm `data-consent="external"` rồi gọi `SolarAnalytics.start()`. Các tên API `grantConsent`/`revokeConsent` được giữ để tương thích bản cũ. Nhấp link `tel:` tự được đặt tên **Bấm gọi điện**; không ghi số điện thoại và không khẳng định cuộc gọi đã kết nối. Bộ mã không bật yêu cầu quyền micro, camera, vị trí hay truy cập tệp.

## Phạm vi và giới hạn triển khai

- Chỉ dùng trên trang có đường dẫn không chứa dữ liệu cá nhân; không gắn vào trang quản trị, tài khoản, thanh toán hoặc URL chứa token/định danh. Query và fragment bị loại, nhưng dữ liệu cá nhân trong pathname vẫn có thể bị ghi.
- Không hỗ trợ định tuyến SPA bằng hash; SPA dùng pathname được hỗ trợ.
- Báo cáo dùng ngày UTC, tối đa 50.000 sự kiện/lần và 200 phiên trong danh sách. Thu nhỏ khoảng thời gian khi đạt giới hạn.
- Dữ liệu giữ 90 ngày; có thể đặt `ANALYTICS_RETENTION_DAYS` từ 1–365. Dọn dữ liệu diễn ra lúc nhận batch tiếp theo.
- Máy chủ phù hợp thử nghiệm và lưu lượng nhỏ; cần giới hạn ở proxy, giám sát, sao lưu và kiểm tra tải trước khi mở rộng. Không dùng như hệ thống analytics quy mô lớn.
- Mã quản trị mặc định đổi mỗi lần khởi động. Đặt biến môi trường để giữ mã cố định. Đóng tab hoặc Khóa báo cáo sẽ xóa mã khỏi bộ nhớ giao diện.

Không có thay đổi nào được thực hiện trên website đang chạy. Sau khi cấu hình server, dùng tab Network để kiểm tra POST `/collect` trả 200 và đối chiếu các sự kiện trong báo cáo.
