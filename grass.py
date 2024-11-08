import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
import websockets  # Untuk koneksi WebSocket
from websockets_proxy import Proxy, proxy_connect  # Untuk koneksi WebSocket dengan proxy
import subprocess  # Untuk menjalankan perintah shell

def print_colored(color_code, text):
    print(f"\033[{color_code}m{text}\033[0m")

def display_colored_text():
    print_colored("40;96", "============================================================")
    print_colored("42;37", "=======================  J.W.P.A  ==========================")
    print_colored("45;97", "================= @AirdropJP_JawaPride =====================")
    print_colored("43;30", "=============== https://x.com/JAWAPRIDE_ID =================")
    print_colored("41;97", "============= https://linktr.ee/Jawa_Pride_ID ==============")
    print_colored("44;30", "============================================================")

async def connect_to_wss(user_id, socks5_proxy=None):
    device_id = str(uuid.uuid4())
    logger.info(f"ID Perangkat: {device_id} untuk User ID: {user_id}")

    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0))  # Jeda acak antar koneksi
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4444/"

            if socks5_proxy:
                # Koneksi dengan proxy
                proxy = Proxy.from_url(socks5_proxy)
                connect_func = proxy_connect(uri, proxy=proxy, ssl=ssl_context, extra_headers={
                    "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
                    "User-Agent": custom_headers["User-Agent"]
                })
            else:
                # Koneksi tanpa proxy
                connect_func = websockets.connect(uri, ssl=ssl_context, extra_headers={
                    "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
                    "User-Agent": custom_headers["User-Agent"]
                })

            async with connect_func as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}
                        })
                        logger.debug(f"Mengirim PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(random.uniform(3, 8))  # Interval ping acak 3-8 detik

                send_ping_task = asyncio.create_task(send_ping())
                
                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(f"Pesan Diterima: {message}")
                        
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
                            logger.debug(f"Mengirim respons AUTH: {auth_response}")
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(f"Mengirim respons PONG: {pong_response}")
                            await websocket.send(json.dumps(pong_response))
                            

                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"Kesalahan: {str(e)}")
            continue

async def main():
    # Menampilkan teks berwarna
    display_colored_text()
    time.sleep(5)  # Jeda selama 5 detik

    # Membaca user_id dari file akun.txt
    with open('akun.txt', 'r') as file:
        user_ids = file.read().splitlines()

    # Membaca proxy dari file proxy.txt
    with open('proxy.txt', 'r') as file:
        all_proxies = file.read().splitlines()
    
    # Penggunaan proxy secara acak untuk setiap user
    assigned_proxies = {}
    tasks = []

    for user_id in user_ids:
        # Pilih proxy acak yang belum digunakan
        available_proxies = list(set(all_proxies) - set(assigned_proxies.values()))
        if not available_proxies:
            logger.error("Tidak ada proxy yang tersedia.")
            break

        selected_proxy = random.choice(available_proxies)
        assigned_proxies[user_id] = selected_proxy

        # Mulai koneksi untuk user_id dengan proxy yang dipilih
        task = asyncio.create_task(connect_to_wss(user_id, selected_proxy))
        tasks.append(task)

        # Jeda 3-5 detik sebelum memulai koneksi user berikutnya
        await asyncio.sleep(random.uniform(3, 5))

    # Tunggu semua koneksi berjalan
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
