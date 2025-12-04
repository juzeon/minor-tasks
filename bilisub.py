import requests
import re
import os
import sys

# 尝试导入 pycookiecheat，如果失败则设置一个标志位
try:
    from pycookiecheat import firefox_cookies
    PYCOOKIECHEAT_AVAILABLE = True
except ImportError:
    PYCOOKIECHEAT_AVAILABLE = False

# 设置请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}

def get_bilibili_cookies():
    """
    尝试从Firefox获取Bilibili的cookies。
    """
    if not PYCOOKIECHEAT_AVAILABLE:
        print("提示: 未安装 'pycookiecheat' 库，将以未登录状态请求。")
        print("若需使用登录功能，请运行: pip install pycookiecheat")
        return None
    
    try:
        print("正在尝试从Firefox获取Bilibili cookies...")
        # 目标URL的域名必须正确，以便找到对应的cookie
        url = 'https://www.bilibili.com'
        cookies = firefox_cookies(url)
        
        if not cookies:
            print("警告: 未在Firefox中找到Bilibili的cookies，将以未登录状态请求。")
            return None
            
        print("成功获取Firefox cookies！")
        return cookies
    except Exception as e:
        print(f"错误: 从Firefox获取cookies失败。原因: {e}")
        print("请确保Firefox已关闭，或检查pycookiecheat的依赖是否正确安装。")
        print("将以未登录状态继续...")
        return None

def parse_bilibili_url(url):
    """
    从Bilibili视频URL中解析出bvid和p号。
    """
    bvid_match = re.search(r'/(BV[a-zA-Z0-9]+)', url)
    if not bvid_match:
        print("错误：无法在URL中找到有效的bvid。")
        return None, None
    bvid = bvid_match.group(1)

    p_match = re.search(r'[?&]p=(\d+)', url)
    page_number = int(p_match.group(1)) if p_match else 1
    
    print(f"解析成功: bvid={bvid}, p={page_number}")
    return bvid, page_number

def get_cid_and_title(bvid, page_number, cookies=None):
    """
    根据bvid和p号获取对应的cid和分P标题。
    """
    api_url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
    print(f"第一步：正在获取视频信息 -> {api_url}")
    
    try:
        response = requests.get(api_url, headers=HEADERS, cookies=cookies)
        response.raise_for_status()
        data = response.json()

        if data['code'] != 0:
            print(f"错误：获取视频信息失败。原因: {data['message']}")
            return None, None

        for part in data['data']:
            if part['page'] == page_number:
                cid = part['cid']
                part_title = part['part']
                print(f"获取成功: cid={cid}, 标题='{part_title}'")
                return cid, part_title
        
        print(f"错误：未找到p={page_number}对应的分P。")
        return None, None

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None, None
    except KeyError:
        print("错误：API返回的JSON格式不符合预期。")
        return None, None

def get_subtitle_url(bvid, cid, cookies=None):
    """
    根据bvid和cid获取AI字幕的URL。
    """
    api_url = f"https://api.bilibili.com/x/player/wbi/v2?bvid={bvid}&cid={cid}"
    print(f"第二步：正在获取播放器信息（包含字幕链接） -> {api_url}")

    try:
        response = requests.get(api_url, headers=HEADERS, cookies=cookies)
        response.raise_for_status()
        data = response.json()

        if data['code'] != 0:
            print(f"错误：获取播放器信息失败。原因: {data['message']}")
            return None

        subtitles = data.get('data', {}).get('subtitle', {}).get('subtitles', [])
        if not subtitles:
            print("未找到可用字幕。")
            return None

        subtitle_info = subtitles[0]
        subtitle_url = subtitle_info.get('subtitle_url')
        
        if not subtitle_url:
            print("错误：字幕信息中缺少URL。")
            return None
            
        if subtitle_url.startswith('//'):
            subtitle_url = 'https:' + subtitle_url
        
        print(f"获取字幕链接成功: {subtitle_url}")
        return subtitle_url

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None
    except (KeyError, IndexError):
        print("错误：API返回的JSON格式不符合预期，或未找到字幕列表。")
        return None

def download_and_save_subtitles(subtitle_url, title, cookies=None):
    """
    下载字幕内容并保存为txt文件。
    """
    print("第三步：正在下载并解析字幕文件...")
    
    try:
        response = requests.get(subtitle_url, headers=HEADERS, cookies=cookies)
        response.raise_for_status()
        subtitle_data = response.json()

        contents = [item['content'] for item in subtitle_data.get('body', [])]
        
        if not contents:
            print("字幕文件为空或格式不正确。")
            return

        safe_filename = re.sub(r'[\\/*?:"<>|]', "_", title) + ".txt"
        
        with open(safe_filename, 'w', encoding='utf-8') as f:
            for line in contents:
                f.write(line + '\n')
        
        print(f"字幕提取完成！已保存到文件: '{os.path.abspath(safe_filename)}'")

    except requests.exceptions.RequestException as e:
        print(f"下载字幕文件时出错: {e}")
    except (KeyError, TypeError):
        print("错误：字幕JSON文件格式不正确。")
    except Exception as e:
        print(f"保存文件时发生未知错误: {e}")


def main():
    """
    主函数
    """
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        print("no arg")
        return

    print(f"开始处理URL: {target_url}")
    print("="*50)
    
    # 在所有操作开始前，先获取cookies
    cookies = get_bilibili_cookies()
    
    print("="*50)
    
    bvid, page_number = parse_bilibili_url(target_url)
    if not bvid:
        return

    # 将获取到的cookies传递给后续所有请求函数
    cid, part_title = get_cid_and_title(bvid, page_number, cookies=cookies)
    if not cid:
        return

    subtitle_url = get_subtitle_url(bvid, cid, cookies=cookies)
    if not subtitle_url:
        return

    download_and_save_subtitles(subtitle_url, part_title, cookies=cookies)


if __name__ == '__main__':
    main()
