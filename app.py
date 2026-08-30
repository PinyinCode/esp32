from datetime import datetime, timedelta
import os
import certifi
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CẤU HÌNH MONGODB VỚI CERTIFI ---
MONGO_URI = os.environ.get("MONGO_URI", "")
client = None
db = None
devices_collection = None

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        tls=True,
        tlsCAFile=certifi.where(),
    )
    client.admin.command("ping")
    db = client["esp32_manager"]
    devices_collection = db["devices"]
    print(">>> KẾT NỐI MONGODB THÀNH CÔNG VỚI CERTIFI! <<<")
except Exception as e:
    print(f">>> LỖI KẾT NỐI MONGODB: {e} <<<")

# --- CẤU HÌNH GITHUB OAUTH ---
GITHUB_CLIENT_ID = "Ov23liD2PKCxgNkZfUj5"
GITHUB_CLIENT_SECRET = "158a74d6beed0ed201ad9a7c4a041738d3185eb6"
YOUR_GITHUB_USERNAME = "PinyinCode"

# Link file firmware .bin chính thức của bạn
DEFAULT_FIRMWARE_URL = "https://esp32-z1t9.onrender.com/xiaozhi.bin"
DEFAULT_LATEST_VERSION = "v1.1.0"


def get_device(mac):
    try:
        if devices_collection is not None:
            doc = devices_collection.find_one({"_id": mac})
            if doc:
                return {
                    "username": doc.get("username", ""),
                    "status": doc.get("status", "active"),
                    "expires_at": doc.get("expires_at", ""),
                    "trial": doc.get("trial", False),
                    "ota_pending": doc.get("ota_pending", False),
                    "created_at": doc.get("created_at", ""),
                }
    except Exception as e:
        print(f"Lỗi khi tìm thiết bị {mac}: {e}")
    return None


def save_device(mac, data):
    try:
        if devices_collection is not None:
            devices_collection.update_one({"_id": mac}, {"$set": data}, upsert=True)
    except Exception as e:
        print(f"Lỗi khi lưu thiết bị {mac}: {e}")


# --- API KIỂM TRA CẬP NHẬT OTA (ĐÃ VÁ LỖI BẢO MẬT) ---
@app.route("/api/check-update", methods=["GET"])
def check_update():
    mac_address = request.args.get("mac")
    if not mac_address:
        return jsonify({"update_available": False, "error": "Missing MAC"}), 400

    mac_address = mac_address.upper()
    device_info = get_device(mac_address)

    # 1. MAC lạ không có trong database -> Từ chối cập nhật ngay lập tức
    if not device_info:
        print(f"Từ chối cập nhật cho MAC lạ: {mac_address}")
        return jsonify({"update_available": False, "message": "Device not registered."})

    # 2. Kiểm tra hạn sử dụng bản quyền
    now = datetime.utcnow()
    try:
        expiry_time = datetime.fromisoformat(device_info["expires_at"])
    except Exception:
        expiry_time = now

    if now > expiry_time:
        device_info["status"] = "expired"
        device_info["ota_pending"] = False
        save_device(mac_address, device_info)
        return jsonify({
            "update_available": False,
            "message": "License expired. Update denied."
        })

    # 3. Chỉ cho phép cập nhật khi còn hạn và có bật cờ yêu cầu OTA (ota_pending = True)
    if device_info.get("ota_pending", False):
        # Tắt cờ ota_pending sau khi thiết bị đã nhận lệnh cập nhật
        device_info["ota_pending"] = False
        save_device(mac_address, device_info)

        return jsonify({
            "update_available": True,
            "latest_version": DEFAULT_LATEST_VERSION,
            "firmware_url": DEFAULT_FIRMWARE_URL,
            "changelog": "Cập nhật thành công theo yêu cầu.",
        })

    return jsonify({"update_available": False, "message": "No update pending."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
