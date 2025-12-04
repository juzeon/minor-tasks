import json
import subprocess
import os
import tempfile
import sys

# ================= 配置区域 =================
SOURCE_REMOTE = 'gdrive:Google AI Studio'
DEST_REMOTE = 'gdrive:aistudio-assets'
KEEP_MIMETYPE = "application/vnd.google-makersuite.prompt"
# ===========================================

def main():
    print(f"正在获取文件列表: {SOURCE_REMOTE} ...")
    
    # 1. 运行 rclone lsjson 获取文件列表
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
        print(f"❌ 执行 rclone 出错:\n{e.stderr}")
        return
    except json.JSONDecodeError:
        print("❌ 解析 JSON 失败，请检查 rclone 输出。")
        return

    # 2. 筛选需要移动的文件
    files_to_move = []
    for item in files:
        # 忽略文件夹
        if item.get("IsDir", False):
            continue
        
        # 如果 MimeType 不是 prompt 类型，则加入移动列表
        if item.get("MimeType") != KEEP_MIMETYPE:
            files_to_move.append(item["Path"])

    # 如果没有文件需要移动
    if not files_to_move:
        print("✅ 没有发现需要移动的非 Prompt 文件。")
        return

    print(f"🔍 发现 {len(files_to_move)} 个文件需要移动:")
    for path in files_to_move:
        print(f"  - {path}")

    # 3. 创建临时文件列表供 --files-from 使用
    # 使用 files-from 模式比循环运行 rclone move 快得多
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tf:
        for path in files_to_move:
            tf.write(path + "\n")
        temp_list_path = tf.name

    try:
        print(f"\n🚀 开始移动文件到 {DEST_REMOTE} ...")
        
        # 4. 执行批量移动命令
        move_cmd = [
            "rclone", "move",
            SOURCE_REMOTE,
            DEST_REMOTE,
            "--files-from", temp_list_path,
            "-v",          # 显示详细信息
            "--progress"   # 显示进度条
        ]
        
        # 在子进程中执行
        subprocess.run(move_cmd, check=True)
        print("\n✅ 所有文件移动完成。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 移动过程中发生错误。")
    finally:
        # 清理临时文件
        if os.path.exists(temp_list_path):
            os.remove(temp_list_path)

if __name__ == "__main__":
    main()