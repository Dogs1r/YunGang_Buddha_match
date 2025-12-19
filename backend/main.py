import sys
import os

# 将项目根目录添加到 sys.path，解决模块导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from backend.config import TEMP_DIR, DB_PATH, PROCESSED_BUDDHA_IMAGE_DIR
from backend.face_api.baidu_api import baidu_face_match, get_access_token
from backend.data_process.db_operation import connect_db
import base64


app = Flask(__name__)

# 跨域配置（复用历史代码）
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 匹配接口
@app.route("/match_face", methods=["POST"])
def match_face():
    try:
        image_base64 = request.json.get("image_base64")
        if not image_base64:
            return jsonify({"code": -1, "msg": "未上传图片"})
        
        # 临时保存图片
        user_image_path = os.path.join(TEMP_DIR, "temp_user.jpg")
        with open(user_image_path, "wb") as f:
            f.write(base64.b64decode(image_base64))
        
        # 调用匹配逻辑
        best_match = match_user_face_to_buddha(user_image_path)
        
        if best_match:
            return jsonify({"code": 0, "data": best_match})
        else:
            return jsonify({"code": -2, "msg": "匹配失败"})
    except Exception as e:
        return jsonify({"code": -3, "msg": f"服务器错误：{str(e)}"})

# 匹配核心函数
def match_user_face_to_buddha(user_image_path):
    # 获取Access Token (一次获取多次使用)
    access_token = get_access_token()
    if not access_token:
        print("无法获取百度API Token")
        return None

    # 查询数据库获取所有佛像信息
    conn, cursor = connect_db(DB_PATH)
    cursor.execute("SELECT * FROM buddha_face_features")
    buddha_records = cursor.fetchall()
    conn.close()
    
    match_results = []
    
    # 遍历佛像库进行1:1比对
    # 注意：如果佛像库很大，这种方式会很慢，建议后续优化为百度Face Search API (1:N)
    for record in buddha_records:
        # 数据库结构: id, buddha_name, cave_number, image_path, face_feature, style, year, description, history
        # 注意：如果数据库是旧的，可能没有 description 和 history，需要处理异常
        try:
            if len(record) == 9:
                buddha_id, name, cave, relative_img_path, _, style, year, description, history = record
            else:
                # 兼容旧数据结构
                buddha_id, name, cave, relative_img_path, _, style, year = record
                description = "暂无描述"
                history = "暂无历史背景"
        except ValueError:
             # 防止解包错误
             continue
        
        # 构建佛像图片的绝对路径
        # 假设 relative_img_path 是相对于 PROCESSED_BUDDHA_IMAGE_DIR 的父级或者就是文件名
        # 根据 batch_extract_feature.py 中的逻辑，relative_path 是相对于项目根目录的
        # 这里我们需要构建出绝对路径
        
        # 尝试直接拼接项目根目录
        # 假设 backend/main.py 在 backend/ 下，项目根目录是 backend/../
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        buddha_image_path = os.path.join(project_root, relative_img_path)
        
        if not os.path.exists(buddha_image_path):
            print(f"佛像图片不存在: {buddha_image_path}")
            continue

        similarity = baidu_face_match(user_image_path, buddha_image_path, access_token)
        
        if similarity > 0: # 只记录有相似度的
            match_results.append({
                "buddha_name": name,
                "cave_number": cave,
                "image_path": relative_img_path, # 返回给前端的路径
                "similarity": round(similarity, 2),
                "style": style,
                "year": year,
                "description": description,
                "history": history
            })

            continue

        similarity = baidu_face_match(user_image_path, buddha_image_path, access_token)
        
        match_results.append({
                "buddha_name": name,
                "cave_number": cave,
                "image_path": relative_img_path, # 返回给前端的路径
                "similarity": round(similarity, 2),
                "style": style,
                "year": year
        })
    
    # 排序返回
    if match_results:
        match_results.sort(key=lambda x: x["similarity"], reverse=True)
        return match_results[0]
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
