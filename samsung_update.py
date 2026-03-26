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
    url = "https://update.internet.apps.samsung.com/service/update2/json"
    req_id = f"{{{uuid.uuid4()}}}"
    sess_id = f"{{{uuid.uuid4()}}}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SamsungInternetUpdater 143.0.0.8",
        "X-Goog-Update-AppId": "ohpjbciplfdockeiligelcjnkiejldpn",
        "X-Goog-Update-Interactivity": "fg",
        "X-Goog-Update-Updater": "updater-143.0.7499.194"
    }

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
                "updatecheck": {"sameversionupdate": True},
                "version": "0.0.0.0"
            }],
            "arch": "x64",
            "dedup": "cr",
            "domainjoined": False,
            "hw": {"avx": True, "physmemory": 16, "sse": True, "sse2": True, "sse3": True, "sse41": True, "sse42": True, "ssse3": True},
            "ismachine": True,
            "os": {"arch": "x86_64", "platform": "Windows", "version": "10.0.26200.8037"},
            "prodversion": "143.0.7499.194",
            "protocol": "4.0",
            "requestid": req_id,
            "sessionid": sess_id,
            "updaterversion": "143.0.7499.194"
        }
    }

    # 1. Đọc phiên bản hiện tại từ file version.txt (nếu có)
    current_version = ""
    if os.path.exists("version.txt"):
        with open("version.txt", "r", encoding="utf-8") as f:
            current_version = f.read().strip()

    print(f"🔍 Đang kiểm tra bản cập nhật... (Phiên bản hiện tại trên kho: {current_version if current_version else 'Chưa có'})")

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()

        raw_text = response.text
        if raw_text.startswith(")]}'"):
            raw_text = raw_text[4:].strip()

        data = json.loads(raw_text)
        app = data.get('response', {}).get('apps', [])[0]

        if 'updatecheck' in app and app['updatecheck'].get('status') == 'ok':
            update_info = app['updatecheck']['pipelines'][0]['operations'][0]
            new_version = app['updatecheck']['nextversion']
            download_url = update_info['urls'][0]['url']
            file_size = update_info['size']

            # 2. So sánh phiên bản
            gh_output = os.environ.get('GITHUB_OUTPUT')
            if new_version == current_version:
                print(f"✅ Phiên bản v{new_version} đang là mới nhất. Sẽ tự động kết thúc phiên làm việc.")
                if gh_output:
                    with open(gh_output, 'a') as f:
                        f.write("update_found=false\n")
                return

            print(f"🚀 PHÁT HIỆN BẢN MỚI: v{new_version}")
            print(f"🔗 Link tải: {download_url}")

            # Lưu vào biến môi trường của GitHub Actions
            if gh_output:
                with open(gh_output, 'a') as f:
                    f.write("update_found=true\n")
                    f.write(f"version={new_version}\n")

            # Cập nhật file version.txt local
            with open("version.txt", "w", encoding="utf-8") as f:
                f.write(new_version)

            filename = f"SamsungInternet_{new_version}.zip"
            extract_folder = f"Samsung_Installer_v{new_version}"

            print(f"📥 Đang tải bộ cài ({file_size // (1024*1024)} MB)...")
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    dl = 0
                    for chunk in r.iter_content(chunk_size=1024*1024): 
                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            done = int(50 * dl / file_size)
                            sys.stdout.write(f"\rTiến trình: [{'█' * done}{'.' * (50-done)}] {dl//(1024*1024)}MB / {file_size//(1024*1024)}MB")
                            sys.stdout.flush()

            print(f"\n📦 Đang giải nén vào '{extract_folder}'...")
            if not os.path.exists(extract_folder):
                os.makedirs(extract_folder)

            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            os.remove(filename)

            print("🎉 HOÀN TẤT TẢI VÀ GIẢI NÉN!")

        else:
            print("❌ Server không trả về thông tin cập nhật.")
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ.get('GITHUB_OUTPUT'), 'a') as f:
                    f.write("update_found=false\n")

    except Exception as e:
        print(f"💥 Lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    auto_update_samsung_internet()
