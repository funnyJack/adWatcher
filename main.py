import random

import pyautogui
import time
import cv2
import numpy as np
import pytesseract
import keyboard

# ================= 配置区（请根据你的环境修改） =================
# Tesseract 安装路径（Windows 用户必须设置，macOS/Linux 注释掉或设为空）
pytesseract.pytesseract.tesseract_cmd = r'D:\software\Tesseract-OCR\tesseract.exe'

# 模板图片路径（请将这些截图放在脚本同目录）
TEMPLATE_WATCH_AD = "watch_ad.png"  # “观看广告+0.25乐豆”按钮
TEMPLATE_CLOSE = "close.png"  # “×”关闭按钮（
TEMPLATE_END="end.png"  #已经看完的灰色图片

# 模板匹配置信度（0~1，越高越严格，推荐0.8~0.9）
CONFIDENCE = 0.6

# 广告加载后等待时间（秒），给广告页面留出加载时间
AD_LOAD_WAIT = 2.0

#广告播放结束后，等待随机时间再进行操作（避免被检测到）
RADOM_TIME_TO_OPERATION= 1 + random.random() # 1 秒到 2 秒之间

# 启动/停止热键
START_KEY = 'F8'
STOP_KEY = 'esc'

# ==============================================================

def find_template(template_path, confidence=CONFIDENCE, grayscale=False):
    """
    在屏幕上查找模板，返回中心坐标，找不到则返回 None
    """
    try:
        location = pyautogui.locateOnScreen(template_path, confidence=confidence, grayscale=grayscale)
        if location:
            center = pyautogui.center(location)
            print(f"找到模板 {template_path}，位置: {center}")
            return center
    except Exception as e:
        print(f"查找模板出错: {e}")
    return None

def click_button(template_path, confidence=CONFIDENCE, grayscale=False):
    """查找模板并点击，返回是否成功"""
    center = find_template(template_path, confidence, grayscale)
    if center:
        pyautogui.click(center)
        print(f"点击 {template_path} 成功")
        return True
    return False

def wait_for_close_button(timeout=60):
    """
    等待广告结束：不断检测“关闭”按钮，并可选检测倒计时为0。
    若检测到按钮则点击并返回 True，超时则返回 False。
    """
    start = time.time()
    #等待 30 秒广告
    print("观看广告中.....")
    time.sleep(30)
    while time.time() - start < timeout:
        #广告时间到了后随机等待 1-2 秒再操作
        time.sleep(RADOM_TIME_TO_OPERATION)
        if click_button(TEMPLATE_CLOSE, confidence=CONFIDENCE):
            print("成功领取奖励！")
            return True
        time.sleep(0.8)  # 降低 CPU 占用
    return False

def main_loop():
    """广告观看主循环"""
    print("开始监听广告页面... 按 ESC 可强制停止")
    cycle = 0
    while True:
        if keyboard.is_pressed(STOP_KEY):
            print("用户停止脚本")
            break
        if find_template(TEMPLATE_END):
            print("恭喜，今日广告已看完，明日再见！")
            break
        cycle += 1
        print(f"\n=== 第 {cycle} 轮 ===")

        # 步骤1：寻找并点击“观看广告”按钮
        if click_button(TEMPLATE_WATCH_AD, confidence=CONFIDENCE):
            print("已点击观看广告，等待广告加载...")
            time.sleep(AD_LOAD_WAIT)  # 等待广告页面出现

            # 步骤2：等待广告结束（跳过/领取按钮出现）后点击关闭
            if wait_for_close_button(timeout=60):
                print("广告已关闭，返回主界面")
                time.sleep(RADOM_TIME_TO_OPERATION)
            else:
                print("警告：超时未检测到跳过按钮，尝试继续下一轮...")
        else:
            print("未找到‘观看广告’按钮，等待1秒后重试...")
            time.sleep(2)

def wait_for_start_key():
    """等待用户按下开始键"""
    print(f"脚本已就绪，请打开微信到广告界面。\n按 {START_KEY} 开始自动观看，按 {STOP_KEY} 随时停止。")
    keyboard.wait(START_KEY)
    print("开始执行自动点击...")

if __name__ == "__main__":
    wait_for_start_key()
    main_loop()