Kiểm tra mã sau xem import os
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)


# Trang chủ: Phục vụ giao diện web nạp code (index.html)
@app.route("/")
def home():
  if os.path.exists("index.html"):
    return send_from_directory(".", "index.html")
  return "OTA Server is running, but index.html is missing!"


# API kiểm tra cập nhật OTA cho ESP32
@app.route("/api/check-update", methods=["GET"])
def check_update():
  print(f"Thiết bị MAC {request.args.get('mac', 'unknown')} đang kiểm tra OTA...")
  return jsonify({
      "update_available": True,
      "firmware_url": f"{request.host_url.rstrip('/')}/download-firmware",
  })


# API cung cấp file .bin cho cả web nạp (trình duyệt tải) và ESP32 (OTA)
@app.route("/download-firmware", methods=["GET"])
def download_firmware():
  return send_from_directory(".", "xiaozhi.bin", as_attachment=True)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
