import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

class StealthBrowser:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None

    def _get_options(self):
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new') # v3.1 建議即使是背景執行也不要開 headless，除非測試
        
        # 基礎反偵測設定
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 視窗大小隨機化 (簡單版)
        options.add_argument('--window-size=1280,800') 
        
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
        # 透過 CDP 執行注入
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": stealth_js}
        )

    def start(self):
        print("🚀 啟動隱形瀏覽器...")
        ### 
        # version_main=None 會自動抓取你電腦當前的 Chrome 版本
        #self.driver = uc.Chrome(options=self._get_options(), version_main=None)
        ###
        # ...
        # 改上面的強制指定版本為 144，對應你目前的瀏覽器版本
        self.driver = uc.Chrome(options=self._get_options(), version_main=144)
        
        # 執行 CDP 注入
        self._inject_cdp_stealth()
        
        # 定位視窗 (不最小化，但移到旁邊)
        self.driver.set_window_position(0, 0)
        print("✅ 瀏覽器就緒，偽裝層已載入")

    def stop(self):
        if self.driver:
            self.driver.quit()

    def goto(self, url):
        self.driver.get(url)

# --- 測試區塊 ---
if __name__ == "__main__":
    browser = StealthBrowser(headless=False) # 開啟視窗模式以便觀察
    browser.start()
    
    # 測試網站：Bot SannySoft (知名的指紋測試站)
    browser.goto("https://bot.sannysoft.com/")
    
    print("測試頁面已開啟，請在 30 秒內檢查 WebDriver 是否顯示為 'missing' (綠色)")
    time.sleep(30)
    browser.stop()