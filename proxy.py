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
    logger.info(device_id)
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
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(60)

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
            logger.error(f"Kesalahan dengan proxy {socks5_proxy}: {str(e)}")
            if any(error_msg in str(e) for error_msg in ["[SSL: WRONG_VERSION_NUMBER]", "invalid length of packed IP address string", "Empty connect reply", "Device creation limit exceeded", "sent 1011 (internal error) keepalive ping timeout; no close frame received"]):
                logger.info(f"Menghapus proxy yang error dari daftar: {socks5_proxy}")
                remove_proxy_from_list(socks5_proxy)
                return None
            else:
                continue

async def main():
    _user_id = 'Ganti User ID Anda DI SINI'
    proxy_file = 'proxy.txt'
    with open(proxy_file, 'r') as file:
        all_proxies = file.read().splitlines()

    active_proxies = random.sample(all_proxies, 100)
    tasks = {asyncio.create_task(connect_to_wss(proxy, _user_id)): proxy for proxy in active_proxies}

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task.result() is None:
                failed_proxy = tasks[task]
                logger.info(f"Menghapus dan mengganti proxy yang gagal: {failed_proxy}")
                active_proxies.remove(failed_proxy)
                new_proxy = random.choice(all_proxies)
                active_proxies.append(new_proxy)
                new_task = asyncio.create_task(connect_to_wss(new_proxy, _user_id))
                tasks[new_task] = new_proxy
            tasks.pop(task)
        for proxy in set(active_proxies) - set(tasks.values()):
            new_task = asyncio.create_task(connect_to_wss(proxy, _user_id))
            tasks[new_task] = proxy

def remove_proxy_from_list(proxy):
    with open("proxy.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            if line.strip() != proxy:
                file.write(line)
        file.truncate()

if __name__ == '__main__':
    display_colored_text()
    asyncio.run(main())
