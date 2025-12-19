import requests
import base64
from backend.config import BAIDU_API_KEY, BAIDU_SECRET_KEY

def get_access_token():
    """
    获取百度AI访问令牌
    """
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    token_params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    try:
        token_resp = requests.post(token_url, params=token_params, timeout=10)
        token_data = token_resp.json()
        if "access_token" not in token_data:
            print(f"获取令牌失败：{token_data}")
            return None
        return token_data["access_token"]
    except Exception as e:
        print(f"❌ 令牌获取失败：{e}")
        return None

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ 读取图片{image_path}失败：{e}")
        return None

def baidu_face_match(user_image_path, buddha_image_path, access_token=None):
    """
    百度AI人脸1:1匹配
    :param user_image_path: 用户人脸图片路径
    :param buddha_image_path: 佛像人脸图片路径
    :param access_token: 可选，如果传入则不重新获取
    :return: 相似度（0-100）
    """
    if not access_token:
        access_token = get_access_token()
    
    if not access_token:
        return 0.0

    user_base64 = image_to_base64(user_image_path)
    buddha_base64 = image_to_base64(buddha_image_path)
    
    if not user_base64 or not buddha_base64:
        return 0.0

    match_url = f"https://aip.baidubce.com/rest/2.0/face/v3/match?access_token={access_token}"
    match_data = [
        {"image": user_base64, "image_type": "BASE64", "face_type": "LIVE"},
        {"image": buddha_base64, "image_type": "BASE64", "face_type": "LIVE"}
    ]
    headers = {"Content-Type": "application/json"}
    
    try:
        match_resp = requests.post(match_url, json=match_data, headers=headers, timeout=10)
        match_result = match_resp.json()

        if match_result.get("error_code") == 0:
            similarity = match_result["result"]["score"]
            return similarity
        else:
            # print(f"❌ 匹配失败：{match_result.get('error_msg')}")
            return 0.0
    except Exception as e:
        print(f"❌ 接口调用异常：{e}")
        return 0.0
