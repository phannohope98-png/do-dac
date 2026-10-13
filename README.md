# Đo Đạc — một mã gắn, nhiều website

Không có màn hình đăng nhập. Màn hình đầu liệt kê tên miền đã gửi dữ liệu. Bấm một website để xem riêng lượt xem, nút gọi/Zalo, bảng trang, luồng chuyển bài, nguồn vào, thiết bị và hành trình từng phiên.

## Mã duy nhất gắn trên mọi website

Sau khi đặt máy chủ nhận tại tên miền HTTPS của bạn, chép cùng đoạn dưới đây trước `</body>` trên từng website:

```html
<script defer src="https://do.tenmiencuaban.vn/tracker.js"></script>
```

Không cần sửa mã cho mỗi web, không cần `data-site`. Tracker tự nhận `location.hostname`. Website xuất hiện sau khi nhận batch đầu tiên (thường khoảng 5 giây). Nếu host mã JS trên CDN riêng, thêm `data-endpoint="https://do.tenmiencuaban.vn/collect"`.

Tự đo lượt xem, link/nút đã nhấp, cuộn 25/50/75/100%, thời gian hoạt động, nguồn và trình duyệt. Link `tel:` tự ghi **Bấm gọi điện**, link Zalo tự ghi **Mở Zalo**. Không lấy số điện thoại trong link, nội dung form, mật khẩu, IP hoặc ảnh màn hình. Không biết cuộc gọi đã kết nối hay tin đã gửi. Không suy ra danh tính và không xác minh người thật/bot. DNT/GPC vẫn được tôn trọng.

Các nút khác có thể đặt nhãn cố định:

```html
<button data-analytics="Xem báo giá">Xem báo giá</button>
<form data-analytics="Yêu cầu khảo sát">...</form>
<a href="/bai-viet/ve-sinh-tam-pin" data-analytics="Bài vệ sinh tấm pin">Đọc bài</a>
```

Form chỉ ghi sự kiện gửi, không lấy giá trị nhập. Để đo gửi thành công, gọi `SolarAnalytics.track('Khảo sát gửi thành công')` sau khi backend trả thành công. `data-analytics-ignore` trên một vùng bỏ qua đo nhấp trong vùng đó. `SolarAnalytics.stop()`/`start()` tắt/bật đo trong tab.

## Chạy thử

Python 3.11+, không cần thư viện ngoài:

```powershell
$env:ANALYTICS_ORIGINS='http://127.0.0.1:8790,http://localhost:8790'
python server.py
```

Mở `http://127.0.0.1:8790/`. Không cần nhập mã hoặc mật khẩu. Mở `/demo`, cuộn và bấm các nút; trở lại báo cáo, Làm mới. Mở thêm `http://localhost:8790/demo` để thử website thứ hai; hai host hiện thành hai website khác nhau.

## Cấu hình máy chủ nhận thật

GitHub Pages chạy giao diện `index.html`, không chạy Python hoặc lưu lượt truy cập. Bộ nhận cần máy chủ riêng HTTPS luôn hoạt động. Hosting chỉ hỗ trợ PHP chưa chạy được backend Python này.

```sh
export ANALYTICS_ORIGINS=https://thesunvn.com.vn,https://www.thesunvn.com.vn,https://websitekhac.vn
export ANALYTICS_REPORT_ORIGINS=https://phannohope98-png.github.io
export ANALYTICS_DB=/var/lib/do-dac/analytics.sqlite
python3 server.py
```

`ANALYTICS_ORIGINS` đăng ký các origin được thu thập, phải đúng scheme + hostname + cổng nếu có. Backend kiểm tra tên miền sự kiện khớp Origin. Đây không phải biện pháp chống giả mạo dữ liệu. `www` và tên miền không `www` được hiển thị riêng. Nếu thêm website, thêm origin vào cấu hình rồi khởi động lại server; đoạn nhúng không đổi.

Đặt reverse proxy HTTPS về `127.0.0.1:8790`, giới hạn request và chạy dưới service. Giữ SQLite ngoài thư mục phục vụ web, sao lưu và đặt thời gian giữ dữ liệu; mặc định 90 ngày, `ANALYTICS_RETENTION_DAYS` từ 1–365. Dọn dữ liệu khi nhận batch tiếp theo.

Trên giao diện GitHub Pages, mở **Mã gắn website & kết nối dữ liệu**, nhập URL HTTPS của máy chủ một lần. Các website xuất hiện tự động từ dữ liệu đã nhận. Mã nhúng được tạo ngay và có nút chép.

**Theo yêu cầu bỏ đăng nhập, API báo cáo không còn xác thực ứng dụng.** Nếu đưa backend ra Internet mà không giới hạn mạng, người biết URL có thể xem báo cáo. Để xem riêng mà không có form đăng nhập ứng dụng, đặt báo cáo sau VPN hoặc quy tắc mạng/proxy; endpoint nhận `/collect` và `/tracker.js` vẫn phục vụ website. CORS không phải cơ chế bảo mật quyền đọc dữ liệu.

## Hiểu báo cáo

- Gọi/Zalo theo trang: biết trang nào dẫn tới liên hệ.
- Bảng đọc và dừng: lượt xem, giây hoạt động trung bình/lượt, số phiên cuộn ít nhất 75%, số phiên có trang này là trang cuối quan sát, số bấm liên hệ.
- Luồng chuyển bài: chuyển trang liên tiếp trong cùng phiên; bỏ lượt tải lại cùng đường dẫn.
- Hành trình: mỗi sự kiện gắn trang và thời gian để xem trình tự.
- Giây hoạt động không chứng minh đọc; trang cuối quan sát không chứng minh đã thoát. Trình chặn/mạng lỗi/DNT/GPC làm số liệu thiếu.
- Loại query và fragment, nhưng không gắn vào trang có thông tin cá nhân trong pathname, tài khoản, thanh toán hoặc trang quản trị. UTM không chứa dữ liệu cá nhân. Google organic keywords xem riêng trong Search Console.
- Báo cáo ngày UTC, tối đa 50.000 sự kiện/website/lần, 200 phiên trong danh sách. Phù hợp thử nghiệm/lưu lượng nhỏ; cần kiểm tra tải trước khi mở rộng. SPA pathname được hỗ trợ; hash route chưa hỗ trợ.

## Kiểm thử

```sh
python -m unittest test_server.py
node test_tracker.cjs
```

9 kiểm thử backend và kiểm thử tracker: nhận đa website, tách dữ liệu, chống tên miền ghi đè, không đăng nhập, giới hạn payload, chống ghi trùng, lọc query/trường không được phép, tự chạy, gọi điện không ghi số, mức cuộn, GPC và tắt/bật.

Bộ mã chưa được gắn vào website công ty. Không chứa dữ liệu đo thử hoặc thông tin đăng nhập hosting trong repository.

## Đo vị trí khách dừng trong bài

Tracker tự lấy các tiêu đề h2/h3 trong main/article làm mốc khu vực. Để rõ và ổn định hơn, gắn tên từng khối nội dung công khai:

```html
<section id="bao-gia" data-analytics-section="Bảng giá lắp đặt">...</section>
<section id="lien-he" data-analytics-section="Liên hệ tư vấn">...</section>
```

Báo cáo ghi tên khu vực tại đường ngang 40% màn hình, vị trí cuộn pixel, chiều cao màn hình, thời gian hoạt động lấy mẫu mỗi 5 giây, tọa độ nhấp và khu vực cuối quan sát khi ẩn/rời. Không ghi toàn bộ văn bản trang hay nội dung nhập. Không dùng tên/tiêu đề vùng chứa thông tin cá nhân. Tiêu đề/DOM thay đổi thì tên vùng tự nhận có thể thay đổi; thuộc tính section giúp giữ nhãn ổn định. Vị trí pixel phụ thuộc kích thước màn hình và bố cục, nên dùng tên khu vực để so sánh. Không ghi chuyển động con trỏ liên tục, không quay màn hình và không suy ra hướng nhìn.
