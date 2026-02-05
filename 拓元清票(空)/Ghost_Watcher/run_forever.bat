@echo off
title 拓元監控守護程式 (Ghost Watcher Guardian)
color 0A

:start
echo ==========================================
echo [%date% %time%] 正在啟動監控機器人...
echo ==========================================

:: 執行 Python 主程式
python main.py

:: 如果程式正常結束 (例如您按 Ctrl+C)，這裡會暫停
echo.
echo ⚠️ 程式已停止！
echo 正在準備於 5 秒後重新啟動... (若要完全停止請直接關閉此視窗)
timeout /t 5

:: 回到開頭重新執行
goto start