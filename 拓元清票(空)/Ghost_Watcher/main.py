import time
import random
import datetime
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 匯入自定義模組
from core.browser_engine import StealthBrowser
from core.scheduler import BrainScheduler
from core.notifier import Notifier
from core.safe_cleaner import kill_specific_chrome_processes

# --- [使用者設定區] ---
TARGET_URLS = [
    "https://tixcraft.com/ticket/area/26_twice/21471",
    "https://tixcraft.com/ticket/area/26_twice/21441"
]

# Discord Webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1468..."

# LINE 設定
LINE_TOKEN = "Y/GxCDgtxCzJ5q+OVQKC..."
LINE_USER_ID = "Ue8c5d5..."

KEYWORDS = ["剩餘", "熱賣中", "Available"]
# --------------------

def get_event_name(driver):
    try:
        full_title = driver.title
        clean_title = full_title.split(" - ")[0]
        return clean_title
    except:
        return "未知場次"

def parse_areas(driver):
    found_tickets = []
    is_urgent = False
    try:
        wait = WebDriverWait(driver, 3)
        area_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".area-list > li, .zone-list > li")))

        for element in area_elements:
            text = element.text.replace("\n", " ")
            if "已售完" in text or "Sold out" in text:
                continue
            for kw in KEYWORDS:
                if kw in text:
                    found_tickets.append(text)
                    if "剩餘" in text: is_urgent = True
                    break
    except Exception as e:
        pass
    return found_tickets, is_urgent

def smart_sleep(engine, wait_time, reason="Gamma 休息"):
    """
    切片睡眠機制
    """
    print(f"😴 {reason} {wait_time} 秒...", end="", flush=True)
    check_interval = 0.5
    loops = int(wait_time / check_interval)

    for _ in range(loops):
        try:
            _ = engine.driver.current_window_handle
        except:
            print("\n")
            raise KeyboardInterrupt("BrowserClosed")
        time.sleep(check_interval)
        print(".", end="", flush=True)

    if (wait_time % check_interval) > 0:
        time.sleep(wait_time % check_interval)
    print("")

def main():
    print("=== 拓元極限隱形監控系統 v3.9 (同步放票極速版) ===")
    print(f"🎯 目標場次數: {len(TARGET_URLS)} 個")
    print(f"⚡ 策略: 發現票券不中斷 -> 掃描全場 -> 統一暫停 5 分鐘")

    # [資源優化] 設定本地資料夾路徑，並進行啟動前清理
    # 這會確保所有資料都存在此資料夾，且不會殘留系統垃圾
    browser_data_dir = os.path.abspath(os.path.join(os.getcwd(), "browser_data"))
    kill_specific_chrome_processes(browser_data_dir)

    brain = BrainScheduler()
    # 傳入本地 profile 路徑，啟用資源隔離
    engine = StealthBrowser(headless=False, user_data_dir=browser_data_dir)

    notifier = Notifier(
        discord_url=DISCORD_WEBHOOK,
        line_token=LINE_TOKEN,
        line_user_id=LINE_USER_ID
    )

    try:
        engine.start()
        notifier.send(f"系統啟動：監控 {len(TARGET_URLS)} 個場次 (v3.9)", level="P1")

        iteration = 1
        while True:
            print(f"\n--- [第 {iteration} 輪巡邏] ---")

            # 標記：這一輪是否有發現任何票？
            any_ticket_found_this_round = False

            for i, url in enumerate(TARGET_URLS):
                try:
                    _ = engine.driver.current_window_handle
                    print(f"🔎 [{i+1}/{len(TARGET_URLS)}] {url.split('/')[-1]} ...", end="")
                    engine.goto(url)

                    tickets, urgent = parse_areas(engine.driver)

                    if tickets:
                        print(" 🚨 有票！(已通知，繼續檢查下一場)")
                        # 標記為真，稍後迴圈結束時再暫停
                        any_ticket_found_this_round = True

                        event_name = get_event_name(engine.driver)
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        header_info = (
                            f"🔥 放票快訊！(Tixcraft)\n"
                            f"場次:{event_name}\n"
                            f"時間:{current_time}\n"
                            f"連結:{url}\n"
                            f"票區：\n"
                        )

                        limit = 1800 - len(header_info)
                        ticket_info = "\n".join(tickets)
                        if len(ticket_info) > limit:
                            ticket_info = ticket_info[:limit] + "\n\n...(略)..."

                        msg_body = header_info + ticket_info

                        # 只要有票就視為 P0 緊急，LINE + Discord 齊發
                        notifier.send(msg_body, level="P0")

                        try:
                            import winsound
                            winsound.Beep(1000, 500) # 嗶一聲 (0.5秒)
                        except:
                            pass

                        # 注意：這裡移除原本的 sleep(60)，讓它繼續跑下一個網址
                    else:
                        print(" 無票", end="")

                    # 切換網址的休息邏輯
                    if i < len(TARGET_URLS) - 1:
                        if any_ticket_found_this_round:
                            # 狀況 A: 前面已經有票了，我們要「急速切換」去檢查下一場 (模擬搶票急迫感)
                            # 設定極短時間 1.5 ~ 2.5 秒
                            switch_delay = random.uniform(1.5, 2.5)
                            print(f" (急速切換: {switch_delay:.1f}s)...")
                        else:
                            # 狀況 B: 沒票，維持原本的悠閒擬人切換 2 ~ 5 秒
                            switch_delay = random.uniform(2.0, 5.0)
                            print(f" (擬人切換: {switch_delay:.1f}s)...")

                        time.sleep(switch_delay)
                    else:
                        print("")

                except Exception as inner_e:
                    error_msg = str(inner_e)
                    if "invalid session id" in error_msg or "disconnected" in error_msg or "window is already closed" in error_msg:
                        raise KeyboardInterrupt("BrowserClosed")
                    print(f"\n⚠️ 暫時性錯誤: {str(inner_e)[:50]}")
                    time.sleep(3)

            # --- 迴圈結束後的決策 ---

            if any_ticket_found_this_round:
                # 如果這一輪有發現票 (不論是第幾個網址)
                # 這裡才進行長時間暫停
                print("\n⚠️⚠️⚠️ 發現票券！系統暫停 300 秒 (5分鐘) 供人工操作...")

                # 發送一個提醒，告知使用者機器人已暫停
                notifier.send("⚠️ 機器人已暫停掃描，請立即手動購票！(5分鐘後恢復)", level="P1")

                # 使用 smart_sleep 防止使用者在這 5 分鐘內關閉視窗程式卻沒反應
                smart_sleep(engine, 300, reason="人工操作暫停")

                # 暫停結束後，清空標記，繼續下一輪
                any_ticket_found_this_round = False
            else:
                # 沒票，進行正常的 Gamma 休息
                wait_time = brain.get_next_wait_time()
                smart_sleep(engine, wait_time)

            iteration += 1

    except KeyboardInterrupt as ke:
        stop_reason = ""
        if str(ke) == "BrowserClosed":
            stop_reason = "偵測到瀏覽器視窗已手動關閉"
            print(f"\n🛑 {stop_reason}，停止監控。")
        else:
            stop_reason = "使用者手動停止 (Ctrl+C)"
            print(f"\n🛑 {stop_reason}")
        notifier.send(f"🛑 監控已停止\n原因: {stop_reason}", level="P1")

    except Exception as e:
        error_msg = str(e)
        if "invalid session id" not in error_msg and "disconnected" not in error_msg:
            print(f"❌ 系統發生未預期崩潰: {e}")
            notifier.send(f"❌ 系統崩潰\n錯誤: {e}", level="P1")
        else:
            print("\n🛑 瀏覽器連線中斷，程式結束。")
            notifier.send("🛑 監控已停止 (瀏覽器連線中斷)", level="P1")

    finally:
        try:
            print("👋 正在清理資源...")
            engine.stop()
            # 結束時可選：再次檢查是否有殘留，確保乾淨退出
            # kill_specific_chrome_processes(browser_data_dir)
            # (註解掉：因為使用者可能想看最後的畫面，或不想在退出時強制殺)
        except:
            pass

if __name__ == "__main__":
    main()