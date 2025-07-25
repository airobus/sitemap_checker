import requests
from bs4 import BeautifulSoup
import time
import os
import json

# 定义 sitemap URL 和存储 URL 的文件
SITEMAP_URL = 'https://play.dictionary.com/sitemap.xml'
URL_FILE = 'urls.txt'
NEW_URLS_FILE = 'new_urls.txt'

def send_push_notification(new_urls):
    """发送推送消息到 pushplus"""
    token = os.environ.get('PUSHPLUS_TOKEN')
    if not token:
        print("错误：找不到环境变量 PUSHPLUS_TOKEN。跳过推送通知。")
        return

    url = "https://www.pushplus.plus/send"
    headers = {"Content-Type": "application/json"}
    content_urls = "\n".join(list(new_urls))
    data = {
      "token": token,
      "title": "Sitemap 发现新 URL",
      "content": f"检测到 {len(new_urls)} 个新增 URL:\n{content_urls}"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("推送消息发送成功。")
    except requests.exceptions.RequestException as e:
        print(f"推送消息发送失败: {e}")

def fetch_sitemap(sitemap_url):
    """获取 sitemap 并提取新增的 URL"""
    print(f"正在从 {sitemap_url} 获取 sitemap...")
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # 【重要改动】明确指定使用 'lxml-xml' 解析器
        soup = BeautifulSoup(response.content, 'lxml-xml')
        current_urls = {url.loc.text for url in soup.find_all('url')}

        existing_urls = set()
        if os.path.exists(URL_FILE):
            with open(URL_FILE, 'r', encoding='utf-8') as f:
                existing_urls = {line.strip() for line in f if line.strip()}

        new_urls = current_urls - existing_urls
        print(f"已获取 {len(current_urls)} 个 URL，发现 {len(new_urls)} 个新增 URL。")

        if new_urls:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(URL_FILE, 'w', encoding='utf-8') as f:
                for url in sorted(list(current_urls)):
                    f.write(url + '\n')
            
            with open(NEW_URLS_FILE, 'a', encoding='utf-8') as f:
                f.write('------------------------\n')
                f.write(f"检查时间: {timestamp}\n")
                for new_url in sorted(list(new_urls)):
                    f.write(new_url + '\n')
                f.write('\n')
            
            print(f"已将 {len(new_urls)} 个新增 URL 记录到 {NEW_URLS_FILE}")
            send_push_notification(new_urls)
        else:
            print("没有发现新的 URL。")

    except requests.exceptions.RequestException as e:
        print(f"获取 sitemap 失败: {e}")
    except Exception as e:
        # 捕获其他可能的异常，例如解析错误
        print(f"处理过程中发生错误: {e}")

if __name__ == "__main__":
    fetch_sitemap(SITEMAP_URL)
