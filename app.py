import os
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)


# Trang chủ (khi truy cập https://esp32-428i.onrender.com/)
@app.route("/")
def home():
  return "Xiaozhi OTA Update Server is Running!"


# API kiểm tra cập nhật mà ESP32 đang gọi tới
@app.route("/api/check-update", methods=["GET"])
def check_update():
  mac = request.args.get("mac", "unknown")
  print(f"Thiết bị có MAC: {mac} đang kiểm tra cập nhật OTA...")

  # Đường dẫn trực tiếp để ESP32 tải file .bin (chính là endpoint download bên dưới)
  firmware_url = "https://esp32-ota-server-9yuy.onrender.com/download-firmware"

  # Trả về JSON thông báo có bản cập nhật mới
  return jsonify({"update_available": True, "firmware_url": firmware_url})


# API phục vụ việc tải file .bin về thiết bị
@app.route("/download-firmware", methods=["GET"])
def download_firmware():
  # Đảm bảo file .bin của bạn trên GitHub đặt tên là xiaozhi.bin
  # (hoặc sửa lại tên file bên dưới cho khớp với tên file .bin bạn đã tải lên)
  return send_from_directory(".", "xiaozhi.bin", as_attachment=True)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
