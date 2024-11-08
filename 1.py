import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect

def print_colored(color_code, text):
    print(f"\033[{color_code}m{text}\033[0m")

def display_colored_text():
    print_colored("40;96", "============================================================")
    print_colored("42;37", "=======================  J.W.P.A  ==========================")
    print_colored("45;97", "================= @AirdropJP_JawaPride =====================")
    print_colored("43;30", "=============== https://x.com/JAWAPRIDE_ID =================")
    print_colored("41;97", "============= https://linktr.ee/Jawa_Pride_ID ==============")
    print_colored("44;30", "============================================================")

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"Device ID: {device_id} untuk User ID: {user_id}")
    
    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0))
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4444/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)

            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, extra_headers={
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
                "User-Agent": custom_headers["User-Agent"]
            }) as websocket:
                
                async def send_ping():
                    while True:
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}
                        })
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(random.uniform(5, 15))  # Jeda acak 5-15 detik

                send_ping_task = asyncio.create_task(send_ping())
                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(message)
                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "4.20.2",
                                    "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                                }
                            }
                            logger.debug(auth_response)
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(pong_response)
                            await websocket.send(json.dumps(pong_response))
                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"Kesalahan dengan proxy {socks5_proxy} untuk User ID {user_id}: {str(e)}")
            await asyncio.sleep(5)  # Tunggu beberapa detik sebelum mencoba kembali
            continue  # Coba ulang koneksi tanpa menghapus proxy

async def main():
    proxy_file = 'proxy.txt'
    user_file = 'akun.txt'

    # Baca User ID dari file akun.txt
    try:
        with open(user_file, 'r') as file:
            user_ids = file.read().splitlines()
    except FileNotFoundError:
        logger.error(f"File {user_file} tidak ditemukan.")
        return

    # Baca Proxy dari file proxy.txt
    try:
        with open(proxy_file, 'r') as file:
            all_proxies = file.read().splitlines()
    except FileNotFoundError:
        logger.error(f"File {proxy_file} tidak ditemukan.")
        return

    if not all_proxies or not user_ids:
        logger.error("Tidak ada proxy atau User ID yang tersedia.")
        return

    display_colored_text()
    
    # Pastikan setiap user_id hanya mendapatkan satu proxy
    active_proxies = random.sample(all_proxies, len(user_ids))
    tasks = []
    for user_id, proxy in zip(user_ids, active_proxies):
        task = asyncio.create_task(connect_to_wss(proxy, user_id))
        tasks.append(task)
        await asyncio.sleep(random.uniform(3, 5))  # Jeda acak antara 3-5 detik sebelum melanjutkan ke akun berikutnya

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
