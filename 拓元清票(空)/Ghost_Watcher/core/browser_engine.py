import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

class StealthBrowser:
    def __init__(self, headless=False, user_data_dir=None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.driver = None

    def _get_options(self):
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')

        # 基礎反偵測設定
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 視窗大小隨機化 (簡單版)
        options.add_argument('--window-size=1280,800')

        # --- 資源優化與垃圾減量設定 ---
        # 禁用日誌，避免大量產生 debug.log
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')

        # 禁用應用程式快取，減少磁碟寫入
        options.add_argument('--disable-application-cache')
        # 限制磁碟快取大小 (例如 1MB)，避免 cache 資料夾無限膨脹
        options.add_argument('--disk-cache-size=1048576')
        # 禁用媒體快取
        options.add_argument('--media-cache-size=1')

        # 其他優化
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')

        # 本地化 Profile (如果有的話，同時設定快取路徑到該目錄下)
        if self.user_data_dir:
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            # 將快取也強制指定到此目錄內，方便管理
            cache_dir = os.path.join(self.user_data_dir, "Cache_Storage")
            options.add_argument(f'--disk-cache-dir={cache_dir}')

        return options

    def _inject_cdp_stealth(self):
        """
        v3.1 核心：CDP 靜態注入
        使用 Page.addScriptToEvaluateOnNewDocument 讓偽裝在所有 JS 執行前生效
        """
        stealth_js = """
        () => {
            // 1. 偽造 WebDriver 屬性 (configurable: false 是關鍵，防止被網站覆寫偵測)
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: false
            });

            // 2. 偽造 Chrome Runtime (讓你看起來像有安裝擴充功能)
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // 3. 偽造 WebGL 廠商 (避開虛擬機特徵)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // 37445 = UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Google Inc. (NVIDIA)'; // 偽裝成有顯卡的電腦
                }
                // 37446 = UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                }
                return getParameter(parameter);
            };

            // 4. 偽造 Permissions (通知權限設為 default 或 prompt，而非 denied)
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        }
        """
        try:
            # 透過 CDP 執行注入
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": stealth_js}
            )
        except Exception as e:
            print(f"⚠️ CDP 注入警告: {e}")

    def start(self):
        print("🚀 啟動隱形瀏覽器...")

        # 使用本地 Profile 時，uc.Chrome 的 user_data_dir 參數建議直接傳入
        # 雖然 options 已經加了 argument，但傳給 uc 建構子更保險
        self.driver = uc.Chrome(
            options=self._get_options(),
            user_data_dir=self.user_data_dir,
            version_main=144, # 保持您原本的設定
            use_subprocess=True # 建議開啟，有助於進程管理
        )

        # 執行 CDP 注入
        self._inject_cdp_stealth()

        # 定位視窗
        try:
            self.driver.set_window_position(0, 0)
        except:
            pass

        print("✅ 瀏覽器就緒，偽裝層已載入")

    def stop(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def goto(self, url):
        if self.driver:
            self.driver.get(url)

# --- 測試區塊 ---
if __name__ == "__main__":
    # 測試時建立一個臨時的資料夾
    test_profile = os.path.join(os.getcwd(), "test_browser_data")
    browser = StealthBrowser(headless=False, user_data_dir=test_profile)
    try:
        browser.start()
        browser.goto("https://bot.sannysoft.com/")
        print("測試頁面已開啟...")
        time.sleep(30)
    finally:
        browser.stop()
