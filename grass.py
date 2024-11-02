import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
import websockets  # Untuk koneksi WebSocket
from websockets_proxy import Proxy, proxy_connect  # Untuk koneksi WebSocket dengan proxy

async def connect_to_wss(user_id, socks5_proxy=None):
    device_id = str(uuid.uuid4())
    logger.info(f"ID Perangkat: {device_id}")
    
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

            # Cek apakah menggunakan proxy atau tidak
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
                        await asyncio.sleep(30)

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
    # Membaca user_id dari file akun.txt
    with open('akun.txt', 'r') as file:
        _user_id = file.readline().strip()  # Mengambil baris pertama dan menghapus spasi

    # Memilih apakah menggunakan proxy atau tidak
    use_proxy = input("Apakah Anda ingin menggunakan proxy? (y/n): ").strip().lower() == 'y'
    
    if use_proxy:
        proxy_file = 'proxy.txt'  # Path ke file proxy Anda
        with open(proxy_file, 'r') as file:
            all_proxies = file.read().splitlines()

        active_proxies = random.sample(all_proxies, 5)  # Jumlah proxy yang ingin digunakan
        tasks = {asyncio.create_task(connect_to_wss(_user_id, proxy)): proxy for proxy in active_proxies}
        
        while True:
            done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                if task.result() is None:
                    failed_proxy = tasks[task]
                    logger.info(f"Proxy gagal dan diganti: {failed_proxy}")
                    active_proxies.remove(failed_proxy)
                    new_proxy = random.choice(all_proxies)
                    active_proxies.append(new_proxy)
                    new_task = asyncio.create_task(connect_to_wss(_user_id, new_proxy))
                    tasks[new_task] = new_proxy
                tasks.pop(task)
            
            # Menambahkan tugas baru jika ada yang selesai
            for proxy in set(active_proxies) - set(tasks.values()):
                new_task = asyncio.create_task(connect_to_wss(_user_id, proxy))
                tasks[new_task] = proxy
    else:
        # Menjalankan koneksi tanpa proxy
        await connect_to_wss(_user_id)

if __name__ == '__main__':
    asyncio.run(main())