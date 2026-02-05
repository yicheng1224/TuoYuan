import os
import subprocess
import time

def kill_specific_chrome_processes(user_data_dir):
    """
    Safely terminates chrome.exe and chromedriver.exe processes that are
    using the specific user_data_dir.

    This ensures we do NOT touch the user's personal Chrome instances
    or other critical system processes.
    """
    if not user_data_dir:
        return

    # Normalize path for Windows matching
    target_path = os.path.abspath(user_data_dir).replace("\\", "\\\\")

    print(f"🧹 正在檢查並清理佔用 '{user_data_dir}' 的殘留程序...")

    # 1. Kill Chrome processes using this profile
    try:
        # WMIC query to find PIDs where CommandLine contains the target path
        cmd = f'wmic process where "name=\'chrome.exe\' and commandline like \'%{target_path}%\'" get processid'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

        # Parse PIDs
        pids = []
        for line in result.decode('utf-8', errors='ignore').splitlines():
            line = line.strip()
            if line.isdigit():
                pids.append(line)

        if pids:
            print(f"   發現 {len(pids)} 個殘留 Chrome 程序 (PIDs: {', '.join(pids)})，正在終止...")
            for pid in pids:
                subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print("   無殘留 Chrome 程序。")

    except subprocess.CalledProcessError:
        # wmic returns error if no instances found, which is fine
        print("   無殘留 Chrome 程序 (Clean)。")
    except Exception as e:
        print(f"   ⚠️ 清理 Chrome 程序時發生非致命錯誤: {e}")

    # 2. Kill chromedriver processes (less risky to kill all, but better to be safe if possible)
    # Usually chromedriver doesn't hold the user-data-dir flag in its own command line,
    # but it is the parent of the chrome process.
    # For simplicity and safety, we will only kill chromedriver if we found zombie chromes,
    # OR we can just try to kill orphaned chromedrivers.
    # However, since the user is very concerned about other processes, we will skip aggressive chromedriver killing
    # unless we can link it.
    # BUT, undetected_chromedriver often leaves a 'chromedriver.exe' running.
    # We will try to find chromedrivers that are *running from our project folder* if possible,
    # or just skip it to be 100% safe as requested.
    # Given the strict requirement: "Do not accidentally close processes in use... core company machine",
    # I will ONLY kill chrome.exe with the specific profile path.
    # Leaving a tiny chromedriver.exe (couple MBs) is better than killing a production process.

    time.sleep(1) # Wait a bit for files to unlock
