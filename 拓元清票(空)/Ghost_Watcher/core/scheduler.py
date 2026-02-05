import numpy as np
from scipy.stats import gamma
import random

class BrainScheduler:
    def __init__(self):
        # Gamma 分佈參數設定
        # a (shape): 形狀參數，決定分佈的偏斜度 (越小越偏左，短時間多)
        # scale: 縮放參數，決定時間的擴散範圍
        # 這些參數設定會讓平均值落在約 30-40 秒，但偶爾會出現 120 秒以上的長尾
        self.shape_param = 2.5 
        self.scale_param = 15.0 

    def get_next_wait_time(self) -> float:
        """
        計算下一次的等待時間 (秒)
        回傳值符合 Gamma 分佈，模擬人類的專注與分心
        """
        # 從 Gamma 分佈取樣
        wait_time = gamma.rvs(a=self.shape_param, scale=self.scale_param, size=1)[0]
        
        # 加入安全邊界 (Clipping)
        # 即使算出來很快，人類極限也不太可能低於 5 秒 (考慮網路載入)
        # 即使算出來很慢，也不要超過 3 分鐘 (避免 Session 過期)
        final_time = max(5.0, min(wait_time, 180.0))
        
        # 加入微小的隨機抖動 (Jitter)，避免浮點數特徵過於完美
        jitter = random.uniform(-0.5, 0.5)
        
        return round(final_time + jitter, 2)

# --- 測試區塊 (執行此檔案可看分佈效果) ---
if __name__ == "__main__":
    scheduler = BrainScheduler()
    print("模擬 10 次人類等待時間：")
    for _ in range(10):
        print(f"{scheduler.get_next_wait_time()} 秒")