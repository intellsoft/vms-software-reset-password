import ctypes
import sys
import urllib.request
import threading
import json
import webbrowser
from packaging import version
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import winreg
import subprocess
import psutil
import glob
import sqlite3
from PIL import Image, ImageTk
import requests
import time
import shutil
import hashlib

# --- بررسی دسترسی Administrator ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # اجرای مجدد برنامه با دسترسی Administrator
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

# کد اصلی برنامه
# --- تابع برای مدیریت مسیر منابع در PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- نسخه فعلی برنامه ---
CURRENT_VERSION = "0.5"

# --- پیکربندی نرم‌افزارها ---
software_configs = {
    "iVMS 4200 version 2": {
        "keyword": "ivms",
        "executables": ["iVMS-4200.exe", "iVMS-4200 Client.exe", "Client\\Client.exe", "Client.exe", "ClientApp.exe", "MainService.exe"],
        "image": "ivms4200-version2.jpg"
    },
    "iVMS 4200 Lite": {
        "keyword": "ivms 4200 lite",
        "executables": ["iVMS-4200 Lite.exe", "iVMS-4200.exe", "Client\\Client.exe", "Client.exe", "ClientApp.exe", "MainService.exe"],
        "image": "ivms4200-lite.jpg"
    },
    "Briton VMS": {
        "keyword": "briton",
        "executables": ["BritonVMSClient.exe", "VMSClient.exe", "Client\\Client.exe", "Client.exe", "BritonVMS.exe", "BRVMS.exe", "BRVMSClient.exe"],
        "image": "briton-vms.jpg"
    },
    "KDT VMS": {
        "keyword": "kdt",
        "executables": ["Kdt Client.exe", "VMSClient.exe", "Client\\Client.exe", "Client.exe", "KDT_VMS.exe", "KDTClientApp.exe", "SecurityVMS.exe"],
        "image": "kdt-vms.jpeg"
    },
    "SmartPSS": {
        "keyword": "smartpss",
        "executables": ["SmartPSS.exe", "SmartPSS Client.exe", "SmartPSSClien.exe", "Configtool.exe", "PMS.exe"],
        "image": "smartpss.jpg"
    },
    "EZStation Uniview old version": {
        "keyword": "ezstation uniview",
        "executables": ["EZStation.exe", "Uniview.exe", "UniviewClient.exe", "EZStationClient.exe", "UniviewService.exe", "EZStationService.exe"],
        "image": "ezstation-old.jpg"
    },
    "uniarch client": {
        "keyword": "uniarch client",
        "executables": ["EZStation.exe", "Uniview.exe", "UniviewClient.exe", "EZStationClient.exe", "UniviewService.exe", "EZStationService.exe"],
        "image": "uniarch-client.jpg"
    },
    "ezstation uniview new version": {
        "keyword": "ezstation uniview new",
        "executables": ["EZStation.exe", "Uniview.exe", "UniviewClient.exe", "EZStationClient.exe", "UniviewService.exe", "EZStationService.exe"],
        "image": "ezstation-new.jpeg"
    },
    "Fara View": {
        "keyword": "fara view",
        "executables": ["FaraView.exe", "FaraVMS.exe", "vms.exe"],
        "image": "faraview.jpg"
    },
    "CMS (H265++ XVR) - no name": {
        "keyword": "cms",
        "executables": ["CMS.exe", "XVR.exe", "H265++.exe", "CMSClient.exe"],
        "image": "cms-h265-plus-xvr.jpg"
    },
    "IMS300": {
        "keyword": "ims300",
        "executables": ["IMS300.exe", "IMSClient.exe", "Client.exe", "Main.exe"],
        "image": "ims300.jpg"
    },
    "CMS3": {
        "keyword": "cms3",
        "executables": ["CMS3.exe", "CMSClient.exe", "Client.exe", "Main.exe"],
        "image": "cms3.jpg"
    }
}

# --- مسیر پوشه حاوی تصاویر ---
IMAGE_FOLDER = "vms"

promotional_links_data = [
    {"text": "نرم افزار تایم لپس دوربین مداربسته", "url": "https://intellsoft.ir/product/timelapse-camera-recorder/"},
    {"text": "نرم افزار تبدیل فیلم دوربین مداربسته تایم لپس", "url": "https://intellsoft.ir/product/time-lapse-software-with-cctv-playback-film/"},
    {"text": "نرم افزار تبدیل عکس به فیلم تایم لپس", "url": "https://intellsoft.ir/product/time-lapse-photo-to-video/"}
]
current_link_index = 0

# --- متغیرهای جدید برای مدیریت پرداخت ---
file_backups = []  # لیست فایل‌های بکاپ شده: (مسیر اصلی, مسیر بکاپ, محتوای اصلی)
payment_authority = None  # کد authority برای تایید پرداخت
payment_verified = False  # وضعیت تایید پرداخت

# --- توابع جدید برای مدیریت بکاپ و بازگردانی ---
def create_backup(file_path):
    """ایجاد بکاپ از فایل و ذخیره مسیر و محتوای آن"""
    try:
        # خواندن محتوای اصلی فایل
        with open(file_path, 'rb') as f:
            original_content = f.read()
        
        # ایجاد نام فایل بکاپ منحصر به فرد
        file_hash = hashlib.md5(original_content).hexdigest()[:8]
        backup_path = f"{file_path}.{file_hash}.backup"
        
        # ذخیره بکاپ
        with open(backup_path, 'wb') as f:
            f.write(original_content)
        
        file_backups.append((file_path, backup_path, original_content))
        return True
    except Exception as e:
        print(f"خطا در ایجاد بکاپ: {e}")
        return False

def restore_backups():
    """بازگردانی تمام فایل‌ها از بکاپ‌ها"""
    global file_backups
    success = True
    
    for original_path, backup_path, original_content in file_backups:
        try:
            # بازگردانی محتوای اصلی
            with open(original_path, 'wb') as f:
                f.write(original_content)
            
            # حذف فایل بکاپ
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            print(f"خطا در بازگردانی فایل: {e}")
            success = False
    
    file_backups = []
    return success

def remove_backups():
    """حذف فایل‌های بکاپ بدون بازگردانی"""
    global file_backups
    for original_path, backup_path, original_content in file_backups:
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
        except Exception as e:
            print(f"خطا در حذف فایل بکاپ: {e}")
    file_backups = []

# --- توابع مربوط به نمایش تصاویر ---
def load_and_display_image(software_name):
    """بارگذاری و نمایش تصویر متناسب با نرم‌افزار انتخاب شده"""
    if software_name in software_configs:
        image_file = software_configs[software_name]["image"]
        try:
            # استفاده از تابع resource_path برای مسیر صحیح
            image_path = resource_path(os.path.join(IMAGE_FOLDER, image_file))
            
            # بارگذاری تصویر با حفظ نسبت ابعاد
            original_image = Image.open(image_path)
            # محاسبه ابعاد جدید متناسب با پنجره
            max_width = 300
            max_height = 200
            width, height = original_image.size
            
            # محاسبه نسبت تغییر اندازه
            width_ratio = max_width / width
            height_ratio = max_height / height
            ratio = min(width_ratio, height_ratio)
            
            new_size = (int(width * ratio), int(height * ratio))
            resized_image = original_image.resize(new_size, Image.LANCZOS)
            
            # تبدیل تصویر برای نمایش در Tkinter
            tk_image = ImageTk.PhotoImage(resized_image)
            
            # به‌روزرسانی لیبل تصویر
            image_label.config(image=tk_image)
            image_label.image = tk_image  # حفظ رفرنس برای جلوگیری از جمع‌آوری توسط GC
            image_label.pack(pady=10)  # نمایش تصویر
            
        except Exception as e:
            # در صورت خطا، پنهان کردن لیبل تصویر
            image_label.pack_forget()
            print(f"خطا در بارگذاری تصویر: {e}")
    else:
        # اگر تصویری یافت نشد، لیبل را پنهان کن
        image_label.pack_forget()

# --- توابع مربوط به بررسی آپدیت ---
def check_for_updates():
    """بررسی وجود نسخه جدید در GitHub"""
    try:
        with urllib.request.urlopen("https://api.github.com/repos/intellsoft/vms-software-reset-password/releases/latest") as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                update_frame.pack(pady=10, fill=tk.X)
                update_label.config(text=f"نسخه جدید {latest_version} موجود است!")
                global download_url
                download_url = data['html_url']
    except Exception as e:
        pass

def download_update(event):
    """باز کردن مرورگر برای دانلود نسخه جدید"""
    webbrowser.open(download_url)

# --- توابع مربوط به ویرایش فایل KDT ---
def process_kdt_config_file(kdt_installation_path):
    config_file_name = "config.ini"
    possible_config_paths = [
        os.path.join(kdt_installation_path, config_file_name),
        os.path.join(kdt_installation_path, "Client", config_file_name),
        os.path.join(kdt_installation_path, "conf", config_file_name),
        os.path.join(kdt_installation_path, "Config", config_file_name)
    ]
    found_config_path = next((p for p in possible_config_paths if os.path.exists(p) and os.path.isfile(p)), None)
    if not found_config_path:
        result_label.config(text=f"فایل {config_file_name} برای KDT VMS پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # ایجاد بکاپ قبل از تغییر
    if not create_backup(found_config_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل پیکربندی")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    new_pwd_value = "3A779DE4EA0B966B5D8EF767EFAFCC20"
    try:
        with open(found_config_path, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            modified = False
            for line in lines:
                if line.strip().lower().startswith("pwd="):
                    f.write(f"pwd={new_pwd_value}\n")
                    modified = True
                else:
                    f.write(line)
            if not modified:
                f.write(f"\npwd={new_pwd_value}\n")
        result_label.config(text="رمز عبور نرم افزار KDT VMS به 123456 تغییر یافت.")
        show_payment_frame()
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل KDT VMS: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع مربوط به SmartPSS ---
def process_smartpss_config_files(smartpss_installation_path):
    files_to_delete = ["conf.xml", "conf.xml.usertmp"]
    smartpss_process_names = [exe.lower() for exe in software_configs["SmartPSS"]["executables"]]
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in smartpss_process_names:
                if proc.info['exe'] and (smartpss_installation_path.lower() in proc.info['exe'].lower() or r"c:\users\public\smartpss".lower() in proc.info['exe'].lower()):
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            pass

    deleted_files = []
    search_base_dirs = [smartpss_installation_path, r"C:\Users\Public\SmartPSS"]
    sub_dirs = ["", "Config", "General", os.path.join("UserData", "Config")]

    # ایجاد بکاپ از فایل‌ها قبل از حذف
    for file_name in files_to_delete:
        for base_dir in search_base_dirs:
            for sub_dir in sub_dirs:
                file_path = os.path.join(base_dir, sub_dir, file_name)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    if create_backup(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_name)
                            break 
                        except (PermissionError, Exception) as e:
                            result_label.config(text=f"خطا در حذف {file_path}: {e}")
                            select_path_button.config(state="enabled")
                            combo_box.config(state="readonly")
                            return
    
    if deleted_files:
        result_label.config(text="رمز عبور نرم افزار SmartPSS ریست شد.")
        show_payment_frame()
    else:
        result_label.config(text="فایل‌های پیکربندی SmartPSS پیدا نشدند.")
    
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به iVMS ---
def process_ivms_config(ivms_installation_path, software_name):
    file_to_delete = "system"
    ivms_process_names = [exe.lower() for exe in software_configs[software_name]["executables"]]
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ivms_process_names:
                if proc.info['exe'] and ivms_installation_path.lower() in proc.info['exe'].lower():
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            pass

    possible_file_paths = [
        os.path.join(ivms_installation_path, file_to_delete),
        os.path.join(ivms_installation_path, "UserData", file_to_delete),
        os.path.join(ivms_installation_path, "data", file_to_delete),
        os.path.join(ivms_installation_path, "Config", file_to_delete)
    ]
    found_file_path = next((p for p in possible_file_paths if os.path.exists(p) and os.path.isfile(p)), None)
    
    if not found_file_path:
        result_label.config(text=f"فایل 'system' برای {software_name} پیدا نشد.")
    else:
        # ایجاد بکاپ قبل از حذف
        if create_backup(found_file_path):
            try:
                os.remove(found_file_path)
                result_label.config(text="رمز نرم افزار حذف شد، نرم افزار را دوباره اجرا کنید.")
                show_payment_frame()
            except Exception as e:
                result_label.config(text=f"خطا در حذف فایل 'system': {e}")
    
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به Briton VMS ---
def process_briton_config_file(briton_installation_path):
    full_config_path = os.path.join(briton_installation_path, "xml", "users.xml")
    if not os.path.exists(full_config_path):
        result_label.config(text=f"فایل users.xml برای Briton VMS پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
        
    # ایجاد بکاپ قبل از تغییر
    if not create_backup(full_config_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل پیکربندی")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    new_users_block = """<USERS>
            <USER name="admin" password="76E0117E3E1D332ECEB2F466D2CE646D" group="administrator" describe="" stop="0" lock="0" />
        </USERS>"""
    try:
        with open(full_config_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            start_index = content.find("<USERS>")
            end_index = content.find("</USERS>")
            if start_index != -1 and end_index != -1:
                new_content = content[:start_index] + new_users_block + content[end_index + len("</USERS>"):]
                f.seek(0)
                f.truncate()
                f.write(new_content)
                result_label.config(text="رمز نرم افزار Briton VMS خالی شد.")
                show_payment_frame()
            else:
                result_label.config(text=f"بلاک <USERS> در فایل users.xml پیدا نشد.")
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل Briton VMS: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع مربوط به EZStation Uniview (نسخه های قدیمی و جدید) و Uniarch ---
def process_uniview_sqlite(db_path, software_name):
    """یک تابع عمومی برای کار با دیتابیس‌های SQLite نرم‌افزارهای Uniview."""
    if not os.path.exists(db_path):
        result_label.config(text=f"فایل دیتابیس در مسیر {db_path} پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # ایجاد بکاپ قبل از تغییر
    if not create_backup(db_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل دیتابیس")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    process_names = [exe.lower() for exe in software_configs[software_name]["executables"]]
    installation_path = os.path.dirname(db_path)
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in process_names:
                if proc.info['exe'] and installation_path.lower() in proc.info['exe'].lower():
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            pass
            
    result_label.config(text=f"پیدا کردن دیتابیس: {db_path}\nدر حال ویرایش...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE tbl_user SET fl_user_password = ? WHERE fl_user_name = ?", ("?XND?NN&?lN0", "admin"))
        if cursor.rowcount > 0:
            conn.commit()
            result_label.config(text="رمز ورود به نرم افزار 123456 با کاربر admin است")
            show_payment_frame()
        else:
            result_label.config(text="کاربر admin در دیتابیس پیدا نشد")
        conn.close()
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش دیتابیس: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

def process_ezstation_old_version(installation_path):
    db_files = glob.glob(os.path.join(installation_path, 'ezsv*.db'))
    if not db_files:
        result_label.config(text="هیچ فایل دیتابیس ezsv*.db پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
    process_uniview_sqlite(db_files[0], "EZStation Uniview old version")

# --- توابع جدید برای Fara View ---
def process_fara_view_config_file(installation_path):
    """ویرایش فایل userinfo.xml برای Fara View"""
    config_file_name = "userinfo.xml"
    possible_config_paths = [
        os.path.join(installation_path, config_file_name),
        os.path.join(installation_path, "vms", "Organization", config_file_name),
        os.path.join(installation_path, "Organization", config_file_name),
        os.path.join(installation_path, "Config", config_file_name)
    ]
    
    found_config_path = next((p for p in possible_config_paths if os.path.exists(p) and os.path.isfile(p)), None)
    if not found_config_path:
        result_label.config(text=f"فایل {config_file_name} برای Fara View پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # ایجاد بکاپ قبل از تغییر
    if not create_backup(found_config_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل پیکربندی")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    new_users_block = """<Users>
        <User id="1" name="admin" pwd="F390D285289ABA20A3F94F9638958F9B" roleID="1" right="ED9CBD7F85EDFBF19473CA8E7BDF2E02" desc="admin user" />
    </Users>"""
    
    try:
        with open(found_config_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            start_index = content.find("<Users>")
            end_index = content.find("</Users>")
            if start_index != -1 and end_index != -1:
                new_content = content[:start_index] + new_users_block + content[end_index + len("</Users>"):]
                f.seek(0)
                f.truncate()
                f.write(new_content)
                result_label.config(text="رمز عبور جدید نرم افزار Fara View: 111111qQ")
                show_payment_frame()
            else:
                result_label.config(text="بلاک <Users> در فایل پیدا نشد.")
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل Fara View: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع جدید برای CMS (H265++ XVR) ---
def process_cms_config_file(installation_path):
    """ویرایش فایل users.xml برای CMS"""
    config_file_name = "users.xml"
    possible_config_paths = [
        os.path.join(installation_path, config_file_name),
        os.path.join(installation_path, "XML", config_file_name),
        os.path.join(installation_path, "Config", config_file_name),
        os.path.join(installation_path, "conf", config_file_name)
    ]
    
    found_config_path = next((p for p in possible_config_paths if os.path.exists(p) and os.path.isfile(p)), None)
    if not found_config_path:
        result_label.config(text=f"فایل {config_file_name} برای CMS پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # ایجاد بکاپ قبل از تغییر
    if not create_backup(found_config_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل پیکربندی")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    new_users_block = """<USERS>
        <USER name="super" password="6B45854AAB919791" group="administrator" describe="" stop="0" lock="0" />
    </USERS>"""
    
    try:
        with open(found_config_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            start_index = content.find("<USERS>")
            end_index = content.find("</USERS>")
            if start_index != -1 and end_index != -1:
                new_content = content[:start_index] + new_users_block + content[end_index + len("</USERS>"):]
                f.seek(0)
                f.truncate()
                f.write(new_content)
                result_label.config(text="رمز عبور جدید نرم افزار CMS: 123456")
                show_payment_frame()
            else:
                result_label.config(text="بلاک <USERS> در فایل پیدا نشد.")
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل CMS: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع جدید برای IMS300 ---
# --- توابع جدید برای IMS300 ---
def process_ims300_database(installation_path):
    """پردازش دیتابیس IMS300 و تغییر رمز عبور"""
    # جستجوی فایل دیتابیس
    db_files = glob.glob(os.path.join(installation_path, 'db_log.db'))
    if not db_files:
        result_label.config(text="فایل دیتابیس db_log.db پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
        
    db_path = db_files[0]
    
    # ایجاد بکاپ قبل از تغییر
    if not create_backup(db_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل دیتابیس")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
        
    # متوقف کردن فرآیندهای مرتبط
    process_names = [exe.lower() for exe in software_configs["IMS300"]["executables"]]
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in process_names:
                if proc.info['exe'] and installation_path.lower() in proc.info['exe'].lower():
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            pass
            
    try:
        # اتصال به دیتابیس SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود جدول و فیلد
        cursor.execute("PRAGMA table_info(table_user)")
        columns = cursor.fetchall()
        column_names = [col[1].lower() for col in columns]
        
        # تعیین نام ستون‌ها بر اساس ساختار واقعی دیتابیس
        username_col = "name"
        password_col = "password"
          
        # به روزرسانی رمز عبور برای کاربر admin
        cursor.execute(f"UPDATE table_user SET [{password_col}] = ? WHERE [{username_col}] = ?", ("123456", "admin"))
        
        if cursor.rowcount == 0:
            # اگر کاربر admin پیدا نشد، سعی می‌کنیم کاربر پیش‌فرض را پیدا کنیم
            cursor.execute(f"SELECT [{username_col}] FROM table_user LIMIT 1")
            default_user = cursor.fetchone()
            if default_user:
                cursor.execute(f"UPDATE table_user SET [{password_col}] = ? WHERE [{username_col}] = ?", ("123456", default_user[0]))
                conn.commit()
                result_label.config(text=f"رمز عبور برای کاربر '{default_user[0]}' به 123456 تغییر یافت.")
                show_payment_frame()
            else:
                result_label.config(text="هیچ کاربری در جدول table_user یافت نشد.")
        else:
            conn.commit()
            result_label.config(text="رمز عبور کاربر admin به 123456 تغییر یافت.")
            show_payment_frame()
            
        conn.close()
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش دیتابیس IMS300: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع جدید برای CMS3 ---
def process_cms3_config_file(installation_path):
    """ویرایش فایل userinfo.xml برای CMS3"""
    # جستجوی مسیر فایل
    possible_paths = [
        os.path.join(installation_path, "User", "admin", "userinfo.xml"),
        os.path.join(installation_path, "User", "userinfo.xml"),
        os.path.join(installation_path, "Config", "userinfo.xml"),
        os.path.join(installation_path, "admin", "userinfo.xml")
    ]
    
    found_config_path = next((p for p in possible_paths if os.path.exists(p) and os.path.isfile(p)), None)
    if not found_config_path:
        result_label.config(text="فایل userinfo.xml برای CMS3 پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # ایجاد بکاپ قبل از تغییر
    if not create_backup(found_config_path):
        result_label.config(text="خطا در ایجاد بکاپ فایل پیکربندی")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
        
    # متوقف کردن فرآیندهای مرتبط
    process_names = [exe.lower() for exe in software_configs["CMS3"]["executables"]]
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in process_names:
                if proc.info['exe'] and installation_path.lower() in proc.info['exe'].lower():
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            pass
            
    try:
        # جایگزینی محتوای فایل
        new_content = """<Userinfo UserName="admin" PicturePath="" UserPhone="" UserPassword="566BD26F08334D98" UserID="0" UserType="1" UserPower="207" />"""
        
        with open(found_config_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        result_label.config(text="رمز عبور جدید نرم افزار CMS3: 123456")
        show_payment_frame()
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل CMS3: {e}")
    finally:
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

# --- توابع اصلی برای نرم‌افزارهای با مسیر ثابت ---
def process_uniarch_client():
    process_uniview_sqlite(r"C:\Users\Public\Uniarch Client\ezsv2.db", "uniarch client")

def process_ezstation_new_version():
    process_uniview_sqlite(r"C:\Users\Public\EZStation\ezsv2.db", "ezstation uniview new version")

# --- تابع تغییر انتخاب نرم‌افزار ---
def on_software_selected(event):
    """هنگام تغییر انتخاب نرم‌افزار، تصویر مربوطه را نمایش بده"""
    selected_software = combo_box.get()
    load_and_display_image(selected_software)

# --- تابع نمایش فریم پرداخت ---
def show_payment_frame():
    """نمایش کادر قرمز برای درخواست پرداخت"""
    payment_frame.pack(pady=10, padx=10, fill=tk.X)
    image_label.pack_forget()  # پنهان کردن تصویر

# --- توابع جدید برای پرداخت ---
def create_payment_request(mobile):
    """ایجاد درخواست پرداخت به زرین‌پال"""
    url = "https://payment.zarinpal.com/pg/v4/payment/request.json"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "merchant_id": "408b3249-02e0-464c-8e74-f324da7a4b5f",
        "amount": "491000",  # 49100 تومان = 491000 ریال
        "callback_url": "https://intellsoft.ir/verify.php",
        "description": "VMS reset password",
        "metadata": {
            "mobile": mobile
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response_data.get('errors'):
            return None, f"خطا: {response_data['errors']}"
            
        if response_data['data'].get('code') == 100:
            # نمایش پاسخ JSON به کاربر
            payment_status_label.config(text=f"درخواست پرداخت ایجاد شد:\n{json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return response_data['data']['authority'], None
        else:
            return None, f"خطا: {response_data['data']['message']}"
            
    except Exception as e:
        return None, f"خطا در ارتباط با سرور: {str(e)}"

def start_payment_verification(authority):
    """شروع فرایند تایید پرداخت هر 15 ثانیه به مدت 2 دقیقه"""
    global payment_verified
    
    # نمایش پیام اولیه
    payment_status_label.config(text="در انتظار پرداخت کاربر...\n\nلطفاً پرداخت را در مرورگر انجام دهید.\n\nپس از پرداخت، این پنجره نبسته شود.")
    
    # تاخیر 2 دقیقه قبل از شروع بررسی
    root.after(120000, lambda: start_verification_checks(authority))

def start_verification_checks(authority):
    """شروع بررسی‌های تناوبی وضعیت پرداخت"""
    payment_status_label.config(text="در حال بررسی وضعیت پرداخت...\n\nلطفاً صبر کنید.")
    
    def verify():
        nonlocal attempts
        if attempts >= 8:  # 2 دقیقه = 8 * 15 ثانیه
            if not payment_verified:
                payment_status_label.config(text="زمان پرداخت به پایان رسید. در صورت پرداخت، لطفاً منتظر بمانید یا با پشتیبانی تماس بگیرید.")
                # بازگردانی تغییرات در صورت عدم پرداخت
                if restore_backups():
                    messagebox.showwarning("خطا", "پرداخت تایید نشد. تغییرات برگردانده شد.")
                else:
                    messagebox.showerror("خطا", "پرداخت تایید نشد و بازگردانی تغییرات با مشکل مواجه شد.")
            return
            
        # ارسال درخواست تایید پرداخت
        url = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "merchant_id": "408b3249-02e0-464c-8e74-f324da7a4b5f",
            "amount": "491000",
            "authority": authority
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            # نمایش وضعیت فعلی
            status_text = f"بررسی {attempts + 1} از 8:\n"
            status_text += f"کد وضعیت: {response_data['data'].get('code', 'نامعلوم')}\n"
            status_text += f"پیام: {response_data['data'].get('message', 'نامعلوم')}"
            payment_status_label.config(text=status_text)
            
            if response_data.get('errors'):
                # نمایش خطاها
                error_text = "\n".join([f"{k}: {v}" for k, v in response_data['errors'].items()])
                payment_status_label.config(text=f"خطا در بررسی پرداخت:\n{error_text}")
            elif response_data['data'].get('code') == 100:
                payment_verified = True
                show_thank_you_frame()
                return
            else:
                # نمایش پاسخ کامل برای دیباگ
                debug_info = json.dumps(response_data, indent=2, ensure_ascii=False)
                payment_status_label.config(text=f"وضعیت پرداخت:\n{debug_info}")
                
        except Exception as e:
            payment_status_label.config(text=f"خطا در ارتباط با سرور: {str(e)}")
        
        attempts += 1
        root.after(15000, verify)  # چک مجدد بعد از 15 ثانیه
    
    attempts = 0
    verify()

def on_payment_button_click():
    """هنگام کلیک روی دکمه پرداخت"""
    mobile = mobile_entry.get().strip()
    if not mobile.isdigit() or len(mobile) != 11:
        payment_status_label.config(text="شماره موبایل نامعتبر است. لطفاً شماره 11 رقمی وارد کنید.")
        return
        
    payment_button.config(state="disabled")
    mobile_entry.config(state="disabled")
    payment_status_label.config(text="در حال ایجاد درخواست پرداخت...")
    
    def payment_thread():
        authority, error = create_payment_request(mobile)
        if authority:
            global payment_authority
            payment_authority = authority
            
            # باز کردن لینک پرداخت در مرورگر
            webbrowser.open(f"https://payment.zarinpal.com/pg/StartPay/{authority}")
            
            # شروع فرایند تایید پرداخت پس از 2 دقیقه
            start_payment_verification(authority)
        else:
            payment_status_label.config(text=error)
            payment_button.config(state="normal")
            mobile_entry.config(state="normal")
            
    threading.Thread(target=payment_thread, daemon=True).start()

def show_thank_you_frame():
    """نمایش پیام تشکر پس از تایید پرداخت"""
    # حذف فایل‌های بکاپ
    remove_backups()
    payment_frame.pack_forget()
    thank_you_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
    
# --- تابع اصلی GUI ---
def select_installation_path_and_process():
    selected_software_name = combo_box.get()
    if not selected_software_name:
        result_label.config(text="لطفاً یک نرم‌افزار را انتخاب کنید.")
        return

    # پاک کردن بکاپ‌های قبلی
    global file_backups
    file_backups = []
    
    select_path_button.config(state="disabled")
    combo_box.config(state="disabled")

    # دیکشنری برای نگاشت نام نرم‌افزار به تابع پردازشی آن
    software_processor = {
        "uniarch client": process_uniarch_client,
        "ezstation uniview new version": process_ezstation_new_version,
    }

    # بررسی اینکه آیا نرم‌افزار انتخاب شده تابع پردازشی بدون نیاز به مسیر دارد یا نه
    if selected_software_name in software_processor:
        result_label.config(text=f"در حال پردازش {selected_software_name}...")
        process_thread = threading.Thread(target=software_processor[selected_software_name], daemon=True)
        process_thread.start()
        return

    # اگر نرم‌افزار نیاز به انتخاب مسیر داشت
    result_label.config(text="لطفاً پوشه نصب را انتخاب کنید...")
    folder_path = filedialog.askdirectory(title=f"لطفاً پوشه نصب {selected_software_name} را انتخاب کنید")

    if folder_path:
        result_label.config(text=f"مسیر انتخاب شده: {folder_path}\nدر حال پردازش...")
        path_based_processor = {
            "KDT VMS": process_kdt_config_file,
            "SmartPSS": process_smartpss_config_files,
            "iVMS 4200 Lite": lambda p: process_ivms_config(p, "iVMS 4200 Lite"),
            "iVMS 4200 version 2": lambda p: process_ivms_config(p, "iVMS 4200 version 2"),
            "Briton VMS": process_briton_config_file,
            "EZStation Uniview old version": process_ezstation_old_version,
            "Fara View": process_fara_view_config_file,
            "CMS (H265++ XVR) - no name": process_cms_config_file,
            "IMS300": process_ims300_database,
            "CMS3": process_cms3_config_file
        }
        
        target_func = path_based_processor.get(selected_software_name)
        if target_func:
            process_thread = threading.Thread(target=target_func, args=(folder_path,), daemon=True)
            process_thread.start()
        else:
            result_label.config(text=f"عملیاتی برای {selected_software_name} تعریف نشده است.")
            select_path_button.config(state="enabled")
            combo_box.config(state="readonly")
    else:
        result_label.config(text="انتخاب مسیر لغو شد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

def rotate_links():
    global current_link_index
    link_info = promotional_links_data[current_link_index]
    rotating_link_label.config(text=link_info["text"], cursor="hand2")
    rotating_link_label.bind("<Button-1>", lambda e: webbrowser.open(link_info["url"]))
    current_link_index = (current_link_index + 1) % len(promotional_links_data)
    root.after(5000, rotate_links)

# --- تنظیمات GUI ---
root = tk.Tk()
root.title("Reset VMS software password")
root.geometry("500x800")  # افزایش ارتفاع برای فضای جدید
root.resizable(False, False)

# استایل‌های جدید
style = ttk.Style()
style.configure("Red.TFrame", background="#FFCDD2", borderwidth=2, relief="solid", bordercolor="#F44336")
style.configure("Red.TLabel", background="#FFCDD2", foreground="#B71C1C", font=("B Nazanin", 10, "bold"))
style.configure("Green.TFrame", background="#C8E6C9", borderwidth=2, relief="solid", bordercolor="#4CAF50")
style.configure("Green.TLabel", background="#C8E6C9", foreground="#1B5E20", font=("B Nazanin", 12, "bold"))

# فریم آپدیت
update_frame = ttk.Frame(root)
update_label = tk.Label(update_frame, text="", fg="green", cursor="hand2", font=("B Nazanin", 10, "bold"))
update_label.pack(pady=5)
update_label.bind("<Button-1>", download_update)

ttk.Label(root, text="نرم‌افزار مورد نظر را انتخاب کنید:").pack(pady=10)

software_options = sorted(list(software_configs.keys()))
combo_box = ttk.Combobox(root, values=software_options, state="readonly", width=40)
if software_options:
    combo_box.set(software_options[0])
combo_box.pack(pady=5)

# افزودن رویداد برای تغییر انتخاب نرم‌افزار
combo_box.bind("<<ComboboxSelected>>", on_software_selected)

select_path_button = ttk.Button(root, text="انتخاب مسیر نصب و اجرا", command=select_installation_path_and_process)
select_path_button.pack(pady=10)

result_label = ttk.Label(root, text="پس از انتخاب نرم‌افزار، دکمه بالا را بزنید.", wraplength=450, justify=tk.CENTER)
result_label.pack(pady=10)

# لیبل برای نمایش تصویر
image_label = ttk.Label(root)
load_and_display_image(combo_box.get())  # نمایش تصویر اولیه

# --- فریم جدید برای پرداخت ---
payment_frame = ttk.Frame(root, style="Red.TFrame")
payment_frame.pack_forget()  # ابتدا مخفی

# محتوای فریم پرداخت
warning_label = ttk.Label(payment_frame, 
                         text="پنجره برنامه نبسته شود، زیرا رمز VMS دوباره قفل می شود.\n\n"
                              "ابتدا نرم افزار VMS خود را اجرا کنید و از ریست شدن پسورد آن مطمئن شوید.\n"
                              "سپس از طریق لینک زیر مبلغ 49100 هزار تومان پرداخت نمایید.",
                         style="Red.TLabel", justify="right", wraplength=450)
warning_label.pack(pady=10, padx=10)

mobile_frame = ttk.Frame(payment_frame)
mobile_frame.pack(pady=10)
ttk.Label(mobile_frame, text="شماره موبایل:", style="Red.TLabel").pack(side=tk.RIGHT, padx=5)
mobile_entry = ttk.Entry(mobile_frame, width=15)
mobile_entry.pack(side=tk.RIGHT)
payment_button = ttk.Button(mobile_frame, text="پرداخت", command=on_payment_button_click)
payment_button.pack(side=tk.RIGHT, padx=5)

payment_status_label = ttk.Label(payment_frame, text="", style="Red.TLabel", wraplength=450, justify=tk.LEFT)
payment_status_label.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# --- فریم جدید برای تشکر پس از پرداخت ---
thank_you_frame = ttk.Frame(root, style="Green.TFrame")
thank_you_frame.pack_forget()  # ابتدا مخفی

thank_you_label = ttk.Label(thank_you_frame, 
                           text="پرداخت با موفقیت انجام شد!\n\nاز حمایت شما سپاسگزاریم.\n\n"
                                "نرم افزار VMS شما فعال شده است و می توانید از آن استفاده کنید.",
                           style="Green.TLabel", justify="center")
thank_you_label.pack(pady=30, padx=20)

# فریم پایینی
bottom_frame = ttk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

developer_link = tk.Label(bottom_frame, text="برنامه نویس : محمدعلی عباسپور (نرم افزار تخصصی دوربین مداربسته اینتل سافت)", fg="blue", cursor="hand2")
developer_link.pack()
developer_link.bind("<Button-1>", lambda e: webbrowser.open("https://intellsoft.ir"))

# استایل برای لینک‌های تبلیغاتی
style.configure("Orange.TFrame", background="#FFA500")
style.configure("Orange.TLabel", background="#FFA500", foreground="white", font=("B Nazanin", 10, "bold"))

# فریم لینک‌های چرخان
rotating_link_frame = ttk.Frame(bottom_frame, style="Orange.TFrame")
rotating_link_frame.pack(fill=tk.X, pady=(10,0))
rotating_link_label = tk.Label(rotating_link_frame, text="", bg="#FFA500", fg="white", cursor="hand2", font=("B Nazanin", 10, "bold"))
rotating_link_label.pack(pady=5)

# شروع روتین‌ها
rotate_links()
update_thread = threading.Thread(target=check_for_updates, daemon=True)
update_thread.start()

# مدیریت رویداد بسته شدن پنجره
def on_closing():
    """هنگام بسته شدن پنجره، در صورت عدم تایید پرداخت، تغییرات را بازگردان"""
    if file_backups and not payment_verified:
        if restore_backups():
            messagebox.showinfo("بازگردانی", "تغییرات به دلیل عدم پرداخت موفق بازگردانی شدند")
        else:
            messagebox.showerror("خطا", "خطا در بازگردانی تغییرات")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
