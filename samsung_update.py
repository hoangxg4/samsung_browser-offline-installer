import requests
import json
import urllib3
import uuid
import os
import zipfile
import sys

# Tắt cảnh báo bảo mật SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def auto_update_samsung_internet():
    # Sử dụng URL gốc KHÔNG có cup2key để script sống vĩnh viễn
    url = "https://update.internet.apps.samsung.com/service/update2/json"

    # Tự động tạo ID ngẫu nhiên cho mỗi lần chạy (đánh lừa server là máy mới)
    req_id = f"{{{uuid.uuid4()}}}"
    sess_id = f"{{{uuid.uuid4()}}}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SamsungInternetUpdater 143.0.0.8",
        "X-Goog-Update-AppId": "ohpjbciplfdockeiligelcjnkiejldpn",
        "X-Goog-Update-Interactivity": "fg",
        "X-Goog-Update-Updater": "updater-143.0.7499.194"
    }

    # Payload "vàng" được trích xuất từ log thành công của bạn
    payload = {
        "request": {
            "@os": "win",
            "@updater": "updater",
            "acceptformat": "crx3,download,puff,run,xz,zucc",
            "apps": [{
                "appid": "ohpjbciplfdockeiligelcjnkiejldpn",
                "enabled": True,
                "installdate": -1,
                "installsource": "taggedmi",
                "updatecheck": {"sameversionupdate": True}, # Bắt buộc kiểm tra bản mới
                "version": "0.0.0.0" # Ép tải bản Full cài mới
            }],
            "arch": "x64",
            "dedup": "cr",
            "domainjoined": False,
            "hw": {
                "avx": True, "physmemory": 16, "sse": True, "sse2": True,
                "sse3": True, "sse41": True, "sse42": True, "ssse3": True
            },
            "ismachine": True,
            "os": {
                "arch": "x86_64", "platform": "Windows", "version": "10.0.26200.8037"
            },
            "prodversion": "143.0.7499.194",
            "protocol": "4.0",
            "requestid": req_id,
            "sessionid": sess_id,
            "updaterversion": "143.0.7499.194"
        }
    }

    print("🔍 Đang kết nối server Samsung để dò tìm phiên bản mới nhất...")

    try:
        # Gửi Request hỏi link
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()

        # Xử lý lớp bảo mật )]}'
        raw_text = response.text
        if raw_text.startswith(")]}'"):
            raw_text = raw_text[4:].strip()

        data = json.loads(raw_text)
        app = data.get('response', {}).get('apps', [])[0]

        # Kiểm tra xem server có nhả link không
        if 'updatecheck' in app and app['updatecheck'].get('status') == 'ok':
            update_info = app['updatecheck']['pipelines'][0]['operations'][0]
            version = app['updatecheck']['nextversion']
            download_url = update_info['urls'][0]['url']
            file_size = update_info['size']

            print(f"✅ Đã tìm thấy phiên bản MỚI NHẤT: v{version}")
            print(f"🔗 Link gốc tự động bắt được: {download_url}")

            filename = f"SamsungInternet_{version}.zip"
            extract_folder = f"Samsung_Installer_v{version}"

            print(f"📥 Đang tải bộ cài ({file_size // (1024*1024)} MB)...")

            # Tải file trực tiếp
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    dl = 0
                    for chunk in r.iter_content(chunk_size=1024*1024): # Chunk 1MB
                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            done = int(50 * dl / file_size)
                            sys.stdout.write(f"\rTiến trình: [{'█' * done}{'.' * (50-done)}] {dl//(1024*1024)}MB / {file_size//(1024*1024)}MB")
                            sys.stdout.flush()

            print(f"\n✅ Đã tải xong: {filename}")
            print(f"📦 Đang giải nén vào thư mục '{extract_folder}'...")

            # Giải nén
            if not os.path.exists(extract_folder):
                os.makedirs(extract_folder)

            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            
            # Xóa file nén gốc cho nhẹ máy (tùy chọn)
            os.remove(filename)

            print("\n🎉 AUTO-UPDATE HOÀN TẤT!")
            print(f"👉 File cài đặt Offline của bạn nằm ở: {extract_folder}/mini_installer.exe")

        else:
            print("❌ Server không trả về bản cập nhật. Kết quả:")
            print(json.dumps(data, indent=2))
            print("💡 Có thể server đang bắt buộc xác thực cup2key. Cần add lại cup2key từ Fiddler nếu bị lỗi này.")

    except Exception as e:
        print(f"💥 Lỗi quá trình thực thi: {e}")

if __name__ == "__main__":
    auto_update_samsung_internet()
