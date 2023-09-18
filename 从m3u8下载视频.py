import os
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES

UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"


def get_m3u8_content(url):
    response = requests.get(url, headers={"User-Agent": UA})
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"无法获取M3U8文件内容，状态码：{response.status_code}")


def parse_m3u8(m3u8_content, domain):
    ts_urls = []
    key = None
    lines = m3u8_content.split('\n')
    for line in lines:
        if line.startswith('#EXT-X-KEY'):
            key_line = line.split(',')
            key_url = key_line[1].strip().split('=')[1].strip('"')
            key_response = requests.get(key_url, headers={"User-Agent": UA})
            if key_response.status_code == 200:
                key = key_response.content
        elif line.startswith('#'):
            continue
        elif line:
            ts_urls.append(domain + line.strip())
    return ts_urls, key


def decrypt_ts_file(ts_url, key, output_dir):
    response = requests.get(ts_url, headers={"User-Agent": UA})
    if response.status_code == 200:
        encrypted_data = response.content
        iv = b"0000000000000000"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted_data)
        ts_filename = os.path.join(output_dir, os.path.basename(ts_url))
        with open(ts_filename, 'wb') as ts_file:
            ts_file.write(decrypted_data)
    else:
        raise Exception(f"无法下载或解密TS文件：{ts_url}")


def download_ts_file(ts_url, output_dir):
    ts_filename = os.path.join(output_dir, os.path.basename(ts_url))
    response = requests.get(ts_url, headers={"User-Agent": UA})
    if response.status_code == 200:
        with open(ts_filename, 'wb') as ts_file:
            ts_file.write(response.content)
    else:
        raise Exception(f"无法下载TS文件：{ts_url}")


def download_ts_files(ts_urls, key, output_dir):
    with ThreadPoolExecutor(max_workers=6) as executor:
        for ts_url in ts_urls:
            if key:
                res = executor.map(decrypt_ts_file, ts_url, key, output_dir)
            else:
                res = executor.map(download_ts_file, ts_url, output_dir)
    len(list(res))


def merge_ts_files(output_dir, output_file):
    ts_files = sorted([os.path.join(output_dir, file)
                      for file in os.listdir(output_dir) if file.endswith(".ts")])
    if not ts_files:
        print("没有找到TS文件.")
        return

    ts_file_list = os.path.join(output_dir, "ts_file_list.txt")
    with open(ts_file_list, "w") as file_list:
        for ts_file in ts_files:
            file_list.write(f"file '{ts_file}'\n")
    # E:\音视频\FormatFactory\ffmpeg.exe -f concat -safe 0 -i .\ts_file_list.txt -c copy -y 123456.mp4
    subprocess.call([FFMPEG, "-f", "concat", "-safe", "0",
                    "-i", ts_file_list, "-c", "copy", "-y", output_file])

    merged_video_size = os.path.getsize(output_file)
    if merged_video_size > 1024*1024:
        print(f"合并后的视频文件大小为 {merged_video_size} 字节")
    else:
        print("合并后的视频文件太小，可能出现问题，请检查。")
        return

    # 删除下载的文件
    for ts_file in ts_files:
        os.remove(ts_file) # type: ignore
    os.remove(ts_file_list)


def main(m3u8_url: str, output_dir, output_file):
    # 获取M3U8文件内容
    domain = m3u8_url.rsplit("/", maxsplit=1)[0] + '/'
    m3u8_content = get_m3u8_content(m3u8_url)

    # 解析M3U8文件，提取TS文件链接和解密密钥（如果有）
    ts_urls, key = parse_m3u8(m3u8_content, domain)

    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 如果有解密密钥，解密TS文件
    if key:
        download_ts_files(ts_urls, key, output_dir)
    else:
        # 没有解密密钥，直接下载TS文件
        for ts_url in ts_urls:
            download_ts_file(ts_url, output_dir)

    # 合并TS文件为一个视频文件
    merge_ts_files(output_dir, output_file)


if __name__ == "__main__":
    # 设置M3U8文件URL、输出目录和输出文件
    FFMPEG = r"E:\音视频\FormatFactory\ffmpeg.exe"
    m3u8_url = r"https://vip.ffzy-play2.com/20221213/8238_a10d2494/2000k/hls/mixed.m3u8"
    output_dir = r"D:\Download\video"
    output_filename = "output.mp4"

    # 调用主函数开始下载和合并
    main(m3u8_url, output_dir, output_filename)
