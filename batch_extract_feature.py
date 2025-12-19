# 整合历史代码中的“预处理+入库”逻辑（不再提取特征，改为直接存储路径供API调用）
import os
import json
import csv
from backend.config import RAW_BUDDHA_IMAGE_DIR, PROCESSED_BUDDHA_IMAGE_DIR, DB_PATH
from backend.data_process.image_preprocess import batch_preprocess_buddha_images
from backend.data_process.db_operation import connect_db

def load_buddha_info(csv_path):
    """
    从CSV加载佛像信息
    返回字典: {(cave_number, buddha_name): {'style': style, 'year': year, 'description': desc, 'history': hist}}
    """
    info_dict = {}
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV文件不存在: {csv_path}，将使用默认值")
        return info_dict
        
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['cave_number'].strip(), row['buddha_name'].strip())
                info_dict[key] = {
                    'style': row.get('style', ''),
                    'year': row.get('year', ''),
                    'description': row.get('description', ''),
                    'history': row.get('history', '')
                }
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
    return info_dict

def main():
    # 1. 预处理原始佛像图片
    print("开始预处理佛像图片...")
    batch_preprocess_buddha_images(RAW_BUDDHA_IMAGE_DIR, PROCESSED_BUDDHA_IMAGE_DIR)
    
    # 加载CSV信息
    csv_path = os.path.join(os.path.dirname(__file__), "data", "buddha_info.csv")
    buddha_info_map = load_buddha_info(csv_path)

    # 2. 连接数据库
    conn, cursor = connect_db(DB_PATH)
    
    # 3. 遍历预处理后的图片，入库
    print("开始扫描佛像图片并入库...")
    
    # 先清空旧数据（可选，防止重复）
    # cursor.execute("DELETE FROM buddha_face_features")
    
    for filename in os.listdir(PROCESSED_BUDDHA_IMAGE_DIR):
        if filename.lower().endswith(('.jpg', '.png')):
            # 解析文件名
            name_parts = filename.replace(".jpg", "").replace(".png", "").split("_")
            cave_number = name_parts[0] if len(name_parts)>=1 else ""
            buddha_name = "_".join(name_parts[1:]) if len(name_parts)>=2 else filename
            
            # 从CSV查找信息，找不到则使用默认值
            info = buddha_info_map.get((cave_number, buddha_name), {})
            style = info.get('style', "未知风格")
            year = info.get('year', "未知时期")
            # 如果CSV中没有描述，或者未在CSV中找到该图片，都默认为空字符串
            # 这样前端页面就会显示默认的“云冈石窟珍贵造像...”文案
            description = info.get('description', "")
            history = info.get('history', "")

            image_path = os.path.join(PROCESSED_BUDDHA_IMAGE_DIR, filename)

            
            # 计算相对路径 (相对于项目根目录)
            # 假设项目根目录是当前脚本所在目录
            project_root = os.path.dirname(os.path.abspath(__file__))
            relative_path = os.path.relpath(image_path, project_root)

            # 入库（不再存储特征向量，face_feature字段留空）
            # 检查是否已存在
            cursor.execute("SELECT id FROM buddha_face_features WHERE image_path = ?", (relative_path,))
            if cursor.fetchone():
                # 更新现有记录的风格和年代信息
                cursor.execute(
                    "UPDATE buddha_face_features SET style=?, year=?, description=?, history=? WHERE image_path=?",
                    (style, year, description, history, relative_path)
                )
                print(f"更新信息：{buddha_name}")
                continue

            cursor.execute(
                """
                INSERT INTO buddha_face_features 
                (buddha_name, cave_number, image_path, face_feature, style, year, description, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    buddha_name,
                    cave_number,
                    relative_path, # 存储相对路径
                    "",            # 特征向量为空
                    style,
                    year,
                    description,
                    history
                )
            )
            conn.commit()
            print(f"入库成功：{buddha_name}")
    
    conn.close()
    print("批量处理完成！")



if __name__ == "__main__":
    main()
