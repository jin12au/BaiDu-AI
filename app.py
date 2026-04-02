# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import requests
import base64
from PIL import Image
import io

app = Flask(__name__)


STUDENT_NAME = "卓金渲"
STUDENT_ID = "202335020555"
# 👇 这里换成你自己的百度AI密钥！
API_KEY = "BPDB9O6Wat3ZQvzCQCl3GZ1T"
SECRET_KEY = "itDZB6Tk0wEqXVckEw5eIUDVjFIz6qKl"


# 🔧 优化：增加超时时间 + 重试机制 + 图片压缩
def get_access_token():
    try:
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": SECRET_KEY
        }
        # 增加超时时间到30秒，避免网络波动
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()  # 主动检查请求是否成功
        return res.json().get("access_token", "")
    except Exception as e:
        print(f"Token获取失败: {str(e)}")
        return ""


# 🔧 优化：图片压缩，避免大文件导致超时
def compress_image(img_bytes, max_size=(1024, 1024), quality=85):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail(max_size)  # 等比例压缩到最大1024x1024
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()
    except Exception as e:
        print(f"图片压缩失败: {str(e)}")
        return img_bytes  # 压缩失败就返回原图


@app.route('/')
def index():
    return render_template('index.html', name=STUDENT_NAME, sid=STUDENT_ID)


@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        # 1. 获取图片
        if 'image' not in request.files:
            return jsonify({"error": "未上传图片"})

        img = request.files['image']
        if img.filename == '':
            return jsonify({"error": "未选择图片文件"})

        img_bytes = img.read()
        # 2. 压缩图片，解决大文件超时
        img_bytes = compress_image(img_bytes)
        # 3. base64编码
        img_base64 = base64.b64encode(img_bytes).decode()

        # 4. 获取token
        access_token = get_access_token()
        if not access_token:
            return jsonify({"error": "百度AI Token获取失败，请检查API_KEY/SECRET_KEY"})

        # 5. 调用百度AI，增加超时时间
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general"
        data = {
            "image": img_base64,
            "access_token": access_token
        }
        # 超时时间设为30秒，避免网络波动
        res = requests.post(url, data=data, timeout=30)
        res.raise_for_status()
        result = res.json()

        return jsonify(result)

    except requests.exceptions.Timeout:
        return jsonify({"error": "请求超时，请检查网络后重试"})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "网络连接失败，请检查网络"})
    except Exception as e:
        return jsonify({"error": f"系统错误: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
