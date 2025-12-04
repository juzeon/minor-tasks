import os
import sys

def main():
    # 1. 获取用户输入的路径
    target_dir = input("请输入要搜索的文件夹路径: ").strip()

    # 去除可能存在的引号（防止用户直接拖拽路径进终端带有引号）
    target_dir = target_dir.replace('"', '').replace("'", "")

    # 2. 验证路径有效性
    if not os.path.exists(target_dir):
        print(f"错误: 路径 '{target_dir}' 不存在。")
        return
    if not os.path.isdir(target_dir):
        print(f"错误: '{target_dir}' 不是一个文件夹。")
        return

    files_to_delete = []
    
    # 定义要搜索的后缀
    target_suffixes = ('_1.jpg', '_2.jpg')

    print(f"\n正在搜索 {target_dir} 及其子目录...")

    # 3. 遍历目录查找文件
    for root, dirs, files in os.walk(target_dir):
        for filename in files:
            # 检查文件名是否以指定后缀结尾
            if filename.endswith(target_suffixes):
                full_path = os.path.join(root, filename)
                files_to_delete.append(full_path)

    # 4. 结果处理
    if not files_to_delete:
        print("未找到以 _1.jpg 或 _2.jpg 结尾的文件。")
        return

    # 列出找到的文件
    print(f"\n找到以下 {len(files_to_delete)} 个文件:")
    for file_path in files_to_delete:
        print(f" - {file_path}")

    # 5. 确认删除
    confirm = input("\n是否确认删除以上文件? (输入 y 确认，其他键取消): ").lower()

    if confirm == 'y':
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"已删除: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"删除失败: {file_path} (错误信息: {e})")
        
        print(f"\n操作结束。共删除了 {deleted_count} 个文件。")
    else:
        print("\n用户取消操作，未删除任何文件。")

if __name__ == "__main__":
    main()