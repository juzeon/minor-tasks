import json
import subprocess
import os
import tempfile
import sys
from datetime import datetime, timedelta, timezone

# ================= 配置区域 =================
# 注意：不要在字符串内部加引号，Python subprocess 会处理空格
SOURCE_REMOTE = 'gdrive:Google AI Studio'
DEST_REMOTE = 'gdrive:aistudio-old-prompts'
# ===========================================

def parse_arguments():
    if len(sys.argv) < 2:
        print("❌ 错误: 请提供天数参数。")
        print("用法: python move_old_prompts.py <天数>")
        print("示例: python move_old_prompts.py 30 (移动30天前的文件)")
        sys.exit(1)
    
    try:
        days = int(sys.argv[1])
        if days < 0:
            raise ValueError
        return days
    except ValueError:
        print("❌ 错误: 天数必须是一个正整数。")
        sys.exit(1)

def get_file_time(iso_str):
    # 处理 rclone 返回的 ISO8601 时间格式 (例如: 2025-09-12T12:10:52.561Z)
    # Python 3.11+ 原生支持 Z，为了兼容旧版本，手动替换 Z 为 +00:00
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    except Exception:
        return None

def main():
    days_limit = parse_arguments()
    
    # 计算截止日期 (当前 UTC 时间 - N 天)
    now_utc = datetime.now(timezone.utc)
    cutoff_date = now_utc - timedelta(days=days_limit)
    
    print(f"📅 设定截止时间: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    print(f"📂 正在扫描目录: {SOURCE_REMOTE} ...")

    # 1. 获取文件列表
    try:
        cmd = ["rclone", "lsjson", SOURCE_REMOTE]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            encoding='utf-8'
        )
        files = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ rclone 执行出错:\n{e.stderr}")
        return
    except json.JSONDecodeError:
        print("❌ 解析 JSON 失败。")
        return

    # 2. 筛选过期文件
    files_to_move = []
    
    for item in files:
        # 跳过文件夹
        if item.get("IsDir", False):
            continue
            
        mod_time_str = item.get("ModTime")
        if not mod_time_str:
            continue
            
        file_time = get_file_time(mod_time_str)
        
        # 核心判断逻辑：如果文件时间 早于 截止时间
        if file_time and file_time < cutoff_date:
            files_to_move.append(item)

    if not files_to_move:
        print(f"✅ 没有发现超过 {days_limit} 天的文件。")
        return

    print(f"🔍 发现 {len(files_to_move)} 个旧文件，准备移动:")
    # 打印前5个文件名作为示例
    for item in files_to_move[:5]:
        print(f"  - [{item['ModTime'][:10]}] {item['Path']}")
    if len(files_to_move) > 5:
        print(f"  ... 以及其他 {len(files_to_move) - 5} 个文件")

    # 3. 创建临时列表并移动
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tf:
        for item in files_to_move:
            tf.write(item['Path'] + "\n")
        temp_list_path = tf.name

    try:
        print(f"\n🚀 开始移动到 {DEST_REMOTE} ...")
        move_cmd = [
            "rclone", "move",
            SOURCE_REMOTE,
            DEST_REMOTE,
            "--files-from", temp_list_path,
            "-v",
            "--progress"
        ]
        subprocess.run(move_cmd, check=True)
        print("\n✨ 移动完成！")

    except subprocess.CalledProcessError:
        print("\n❌ 移动过程中发生错误。")
    finally:
        if os.path.exists(temp_list_path):
            os.remove(temp_list_path)

if __name__ == "__main__":
    main()