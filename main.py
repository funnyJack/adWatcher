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
TEMPLATE_SKIP = "skip.png"  # “跳过”按钮
TEMPLATE_CLAIM = "claim.png"  # “领取”按钮
TEMPLATE_CLOSE = "close.png"  # “×”关闭按钮（可选）
TEMPLATE_END="end.png"  #已经看完的灰色图片

# 模板匹配置信度（0~1，越高越严格，推荐0.8~0.9）
CONFIDENCE = 0.6

# 广告加载后等待时间（秒），给广告页面留出加载时间
AD_LOAD_WAIT = 2.0

#广告播放结束后，等待随机时间再进行操作（避免被检测到）
RADOM_TIME_TO_OPERATION= 1 + random.random() # 1 秒到 2 秒之间

# 倒计时数字区域（如果不使用模板，可以手动设定屏幕上的坐标区域，例如右上角）
# 格式：(left, top, width, height)，可运行辅助脚本获取坐标
TIMER_REGION = None  # 例如 (1800, 50, 60, 40)，若为None则不启用OCR计时检测

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


def ocr_digit_in_region(region):
    """
    在指定屏幕区域截图，识别并返回数字（仅数字）。
    region: (left, top, width, height)
    """
    if not region:
        return None
    screenshot = pyautogui.screenshot(region=region)
    # 预处理：转灰度、二值化提高识别率
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 使用 pytesseract 识别数字，只识别 0-9
    config = '--psm 7 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(thresh, config=config).strip()
    if text.isdigit():
        return int(text)
    return None


def wait_for_skip_button(timeout=60):
    """
    等待广告结束：不断检测“跳过/领取/×”按钮，并可选检测倒计时为0。
    若检测到按钮则点击并返回 True，超时则返回 False。
    """
    start = time.time()
    #等待 30 秒广告
    print("观看广告中.....")
    time.sleep(30)
    while time.time() - start < timeout:
        #广告时间到了后随机等待 1-2 秒再操作
        time.sleep(RADOM_TIME_TO_OPERATION)
        # 1. 检查是否出现了可点击的跳过按钮（模板匹配）
        if find_template(TEMPLATE_CLAIM):
            #找到了领取奖励的模板，则尝试点击关闭按钮
            for tmpl in [TEMPLATE_SKIP, TEMPLATE_CLOSE]:
                if click_button(tmpl, confidence=CONFIDENCE):
                    print("成功领取奖励！")
                    return True

        # 2. 如果配置了计时区域，监控倒计时是否归零
        if TIMER_REGION:
            digit = ocr_digit_in_region(TIMER_REGION)
            if digit is not None and digit == 0:
                print("检测到倒计时为0，准备寻找跳过按钮...")
                # 倒计时归零后可能会出现按钮，再尝试一轮
                time.sleep(0.5)
                for tmpl in [TEMPLATE_SKIP, TEMPLATE_CLAIM, TEMPLATE_CLOSE]:
                    if click_button(tmpl, confidence=CONFIDENCE):
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
            if wait_for_skip_button(timeout=60):
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