import argparse
import subprocess
import json
import sys

def human_readable_size(size_bytes):
    """
    将字节大小转换为人类可读的格式 (B, KB, MB, GB, TB)
    """
    if size_bytes == 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    p = float(size_bytes)
    
    while p >= 1024 and i < len(size_name) - 1:
        p /= 1024.0
        i += 1
        
    return f"{p:.2f} {size_name[i]}"

def get_rclone_json(remote_path):
    """
    调用 rclone lsjson -R 获取文件列表
    """
    # 构造命令: rclone lsjson -R (递归) "路径"
    cmd = ["rclone", "lsjson", "-R", remote_path]
    
    try:
        # 执行命令并捕获输出
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: rclone 执行失败。\n错误信息: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 未找到 rclone 命令，请确保已安装并添加到 PATH 中。", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: 无法解析 rclone 返回的 JSON 数据。", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="递归计算 rclone 远程路径下的文件总大小")
    parser.add_argument("path", help="rclone 远程路径 (例如: gdrive:Google AI Studio)")
    args = parser.parse_args()

    print(f"正在扫描: {args.path} ...")
    
    items = get_rclone_json(args.path)
    
    total_size = 0
    file_count = 0
    
    # 表头格式化
    print(f"\n{'大小':>12} | {'文件名'}")
    print("-" * 60)

    # 遍历所有项目
    for item in items:
        # 跳过文件夹，只计算文件
        if item.get("IsDir", False):
            continue
            
        size = item.get("Size", 0)
        name = item.get("Path", "Unknown") # 使用 Path 可以显示相对路径
        
        # 累加大小
        total_size += size
        file_count += 1
        
        # 打印单个文件信息
        print(f"{human_readable_size(size):>12} | {name}")

    print("-" * 60)
    print(f"总文件数: {file_count}")
    print(f"总大小:   {human_readable_size(total_size)}")

if __name__ == "__main__":
    main()