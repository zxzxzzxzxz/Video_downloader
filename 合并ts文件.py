import aiofiles
import asyncio
import os
import re
from Crypto.Cipher import AES


def merge_ts_files(m3u8_file: str, ts_relpath: str = './', encoding="utf-8") -> str:
    m3u8_path = os.path.split(m3u8_file)[0]
    m3u8_name = os.path.split(m3u8_file)[1].split('.')[0]

    os.chdir(m3u8_path)
    os.chdir(ts_relpath)
    ts_match = re.compile(r"[\/]([^\/]+?[.]ts)")
    ts_names = []
    with open(m3u8_file, mode='r', encoding=encoding) as f:
        for line in f.readlines():
            ts_names.append(ts_match.search(line).group(1))
    file_num = len(ts_names)

    for index, ts_name in enumerate(ts_names):
        os.rename(ts_name, f"{index}.ts")
    ts_names = [f"{i}.ts" for i in range(file_num)]
    ts_str = "+".join(ts_names)
    os.system(f"copy /b {ts_str} {m3u8_name}.mp4")
    return "合并ts文件成功"


async def async_decrypt(filename, key: bytes):
    aes = AES.new(key=key, iv=b"0000000000000000", mode=AES.MODE_CBC)
    async with aiofiles.open(filename, mode="rb") as f1, aiofiles.open("decrypted/"+filename, mode="wb") as f2:
        content = await f1.read()
        await f2.write(aes.decrypt(content))
    print(filename+"Decrypted")


async def decrypt(m3u8_file, key: bytes):
    m3u8_path = os.path.split(m3u8_file)[0]
    m3u8_name = os.path.split(m3u8_file)[1].split('.')[0]

    os.chdir(m3u8_path)
    os.makedirs("decrypted", exist_ok=True)
    ts_list = []
    with open(m3u8_name, mode='r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.endswith(".ts"):
                ts_list.append(line.split('/')[-1])
    tasks = [asyncio.create_task(async_decrypt(ts, key)) for ts in ts_list]
    await asyncio.wait(tasks)
    print("All ts files decrypted.")

if __name__ == '__main__':
    key = b"5fb137c9998eb9ff"
    m3u8_file = r"index.m3u8"
    asyncio.run(decrypt(m3u8_file, key))
    print("解密完成")
    # merge_ts_files(m3u8_file=r"D:\视频下载\新建文件夹\m3u8.txt")
