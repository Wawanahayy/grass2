async def main():
    proxy_file = 'proxy.txt'
    user_file = 'akun.txt'

    while True:
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

        # Pastikan tidak menggunakan lebih banyak proxy daripada user ID
        num_proxies_to_use = min(len(all_proxies), len(user_ids))
        active_proxies = random.sample(all_proxies, num_proxies_to_use)

        tasks = {}
        for user_id, proxy in zip(user_ids, active_proxies):
            task = asyncio.create_task(connect_to_wss(proxy, user_id))
            tasks[task] = (proxy, user_id)

        while tasks:
            done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                proxy, user_id = tasks[task]
                tasks.pop(task)
                result = task.result()

                if result is None:  # Jika ada kesalahan
                    logger.info(f"Menghapus dan mengganti proxy yang gagal: {proxy} untuk User ID: {user_id}")
                    # Jika user ID gagal, kita tidak menambahkannya ke daftar gagal
                    # Cukup lanjutkan ke user ID berikutnya
                else:
                    logger.info(f"User ID {user_id} berhasil terhubung dengan proxy {proxy}")

        # Setelah semua task selesai, Anda bisa menambahkan logika di sini
        # Jika ingin menunggu sebelum mencoba kembali, tambahkan delay
        await asyncio.sleep(5)  # Menunggu sebelum mencoba lagi (opsional)

if __name__ == '__main__':
    display_colored_text()
    asyncio.run(main())
