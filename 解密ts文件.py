import asyncio
import aiofiles
from Crypto.Cipher import AES
import os

PATH = r"D:\Download\命运石之门"
os.chdir(PATH)
os.makedirs("decrypted",exist_ok=True)

async def async_decrypt(filename, key):
    aes=AES.new(key=key,iv=b"0000000000000000",mode=AES.MODE_CBC)
    async with aiofiles.open(filename,mode="rb") as f1, aiofiles.open("decrypted/"+filename,mode="wb") as f2:
        content=await f1.read()
        await f2.write(aes.decrypt(content))
    print(filename+"Decrypted")

async def main(m3u8_filename,key):
    filename_list = []
    with open(m3u8_filename, mode='r',encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.endswith(".ts"):
                filename_list.append(line.split('/')[-1])
    tasks=[asyncio.create_task(async_decrypt(i, key)) for i in filename_list]
    await asyncio.wait(tasks)
    
if __name__ == '__main__':
    key=b"5fb137c9998eb9ff"
    m3u8_filename=r"index.m3u8"
    asyncio.run(main(m3u8_filename,key))
    print("解密完成")