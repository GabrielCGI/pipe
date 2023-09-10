import sys
import os
import time
sys.path.append(r"R:\pipeline\networkInstall\arnold\SDK\Arnold-7.2.2.1-windows\python")
from arnold import *
sys.path.append(r"R:\pipeline\networkInstall\python_lib")
import pyautogui
import pyperclip
import subprocess
import pygetwindow as gw
from screeninfo import get_monitors

# Image to locate with pyautogui
DIR_IMG = os.path.join(os.path.dirname(__file__),"arnold_license_img")
SIGNIN_BTN_IMG = os.path.join(DIR_IMG,'signin_btn.png')
VALID_LICENSE = os.path.join(DIR_IMG,'valid_license.png')
INVALID_LICENSE = os.path.join(DIR_IMG,'invalid_license.png')
MAIL_BTN = os.path.join(DIR_IMG,'validate_mail_autodesk.png')
PASSWORD_BTN = os.path.join(DIR_IMG,'validate_password_autodesk.png')
ACCESS_PRODUCT_BTN = os.path.join(DIR_IMG,'access_product_button.png')
ARNOLD_TOP_WINDOW = os.path.join(DIR_IMG,'arnold_top_window.png')
N_TIMEOUT=100

# Credential Autodesk
MAIL=r"hello@illogicstudios.com"
PASSWORD=r"@illogic21"

def get_monitor_info():
    """
    Get the coordinates and the size of the monitor
    """
    x = 0
    y = 0
    w = 1920
    h = 1080
    monitors = get_monitors()
    for m in monitors:
        if m.is_primary:
            x = m.x
            y = m.y
            w = m.width
            h = m.height
            break
    return [x,y,w,h]


def close_arnold_manager_window(force = False):
    """
    Close the Arnold License Manager Window
    """
    arnold_windows = gw.getWindowsWithTitle('Arnold License Manager')
    for arnold_window in arnold_windows:
        arnold_window.close()

def setup_arnold_manager_window(info):
    """
    Set the Arnold License Manager on the primary monitor
    """
    arnold_windows = gw.getWindowsWithTitle('Arnold License Manager')
    while len(arnold_windows) ==0:
        arnold_windows = gw.getWindowsWithTitle('Arnold License Manager')
    arnold_windows[0].moveTo(info[0], info[1])

def check_valid_license():
    """
    Check if a license is registerd
    """
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        valid_license_box = pyautogui.locateOnScreen(VALID_LICENSE)
        invalid_license_box = pyautogui.locateOnScreen(INVALID_LICENSE)
        if valid_license_box and not invalid_license_box:
            print("License Valid Found")
            return True
        elif not valid_license_box and invalid_license_box:
            print("License Not Valid Found")
            return False
        n+=1
        time.sleep(1)
        print(str(n).zfill(3)+" Checking License Validity")

def click_on_signin():
    """
    Click on the Arnold Manager Sign In Button
    """
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        signin_btn_box = pyautogui.locateOnScreen(SIGNIN_BTN_IMG, confidence=0.9)
        if signin_btn_box:
            print("Signin Button Found and Clicked")
            pyautogui.click(x=signin_btn_box[0]+30, y=signin_btn_box[1]+15)
            break
        n+=1
        time.sleep(1)
        print(str(n).zfill(3)+" Finding Signin Button")

def setup_chrome_window(info):
    """"
    Set the chrome window on the primary monitor
    """
    chrome_windows = gw.getWindowsWithTitle('Chrome')
    while len(chrome_windows)==0:
        chrome_windows = gw.getWindowsWithTitle('Chrome')
    print(chrome_windows)
    for chrome_window in chrome_windows:
        chrome_window.restore()
        chrome_window.minimize()
        chrome_window.restore()
        chrome_window.moveTo(info[0], info[1])
        chrome_window.maximize()


def click_and_fill_mail_field_form():
    """
    Fill the mail field
    """
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        autodesk_form_box = pyautogui.locateOnScreen(MAIL_BTN, confidence=0.9)
        signin_btn_box = pyautogui.locateOnScreen(ACCESS_PRODUCT_BTN, confidence=0.9)
        if autodesk_form_box and not signin_btn_box:
            print("Autodesk Username Form Found and Filled")
            pyperclip.copy(MAIL)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'v')
            pyperclip.copy('')
            pyautogui.click(x=autodesk_form_box[0]+50, y=autodesk_form_box[1]+int(autodesk_form_box[3]/2))
            return True
        elif not autodesk_form_box and signin_btn_box:
            print("Access Product Button Found and Clicked")
            pyautogui.click(x=signin_btn_box[0]+30, y=signin_btn_box[1]+15)
            return False
        n+=1
        time.sleep(1)
        print(str(n).zfill(3)+" Finding Autodesk Username Form")

def click_and_fill_password_field_form():
    """
    Fill the password field
    """
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        autodesk_form_box = pyautogui.locateOnScreen(PASSWORD_BTN, confidence=0.9)
        if autodesk_form_box:
            print("Autodesk Password Form Found and Filled")
            pyperclip.copy(PASSWORD)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'v')
            pyperclip.copy('')
            pyautogui.click(x=autodesk_form_box[0]+50, y=autodesk_form_box[1]+int(autodesk_form_box[3]/2))
            break
        n+=1
        time.sleep(1)
        print(str(n).zfill(3)+" Finding Autodesk Password Form")

def click_access_product_button():
    """
    Accept Product to valid the license
    """
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        signin_btn_box = pyautogui.locateOnScreen(ACCESS_PRODUCT_BTN, confidence=0.9)
        if signin_btn_box:
            print("Access Product Button Found and Clicked")
            pyautogui.click(x=signin_btn_box[0]+30, y=signin_btn_box[1]+15)
            break
        n+=1
        print(str(n).zfill(3)+" Finding Access Product Button")


def close_arnold_manager_window_with_ui():
    n=0
    while True:
        if n == N_TIMEOUT: raise Exception("Timeout License Arnold")
        signin_btn_box = pyautogui.locateOnScreen(ARNOLD_TOP_WINDOW, confidence=0.9)
        if signin_btn_box:
            print("Signin Button Found and Clicked")
            pyautogui.click(x=signin_btn_box[0]+signin_btn_box[2]-20, y=signin_btn_box[1]+10)
            break
        n+=1
        time.sleep(1)
        print(str(n).zfill(3)+" Finding Signin Button")

try:

    # Check if license available
    print("Checking License")
    AiBegin()
    license_used = AiLicenseIsAvailable()
    AiEnd()

    if not license_used:
        print("No License")
        # Close Arnold License Manager Window
        close_arnold_manager_window()
        # Start Arnold License Manager
        os.system(r"start R:\pipeline\networkInstall\arnold\7.2.1.0\maya2022\bin\ArnoldLicenseManager.exe")
        # Get the coordinates an size of the primary monitor
        info = get_monitor_info()
        print(info)
        # Set the arnold window to the monitor coordinates
        setup_arnold_manager_window(info)
        print("setup")
        # Check if arnold has a license
        if not check_valid_license() :
            print("start")
            # Click on Signin Button
            click_on_signin()
            # Set the chrome window to the primary monitor
            setup_chrome_window(info)
            # If already connected just accept otherwise fill the mail field
            if click_and_fill_mail_field_form():
                # fill the password field
                click_and_fill_password_field_form()
                # Accept as user
                click_access_product_button()
        # Close the arnold manager
        close_arnold_manager_window_with_ui()
    else:
        print("License Found")
except KeyboardInterrupt:
    print('\n')
except Exception as e:
    print(repr(e))
