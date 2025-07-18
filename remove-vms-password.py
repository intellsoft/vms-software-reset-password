import ctypes
import sys
import urllib.request
import threading
import json
import webbrowser
from packaging import version

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
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import winreg
import os
import subprocess
import threading
import psutil 
import glob
import sqlite3

# --- نسخه فعلی برنامه ---
CURRENT_VERSION = "0.2"

# --- پیکربندی نرم‌افزارها ---
software_configs = {
    # تغییر نام "iVMS" به "iVMS 4200 version 2"
    "iVMS 4200 version 2": {
        "keyword": "ivms", # کلمه کلیدی برای جستجو در رجیستری و مسیرها
        "executables": ["iVMS-4200.exe", "iVMS-4200 Client.exe", "Client\\Client.exe", "Client.exe", "ClientApp.exe", "MainService.exe"]
    },
    "iVMS 4200 Lite": {
        "keyword": "ivms 4200 lite",
        "executables": ["iVMS-4200 Lite.exe", "iVMS-4200.exe", "Client\\Client.exe", "Client.exe", "ClientApp.exe", "MainService.exe"]
    },
    "Briton VMS": {
        "keyword": "briton",
        "executables": ["BritonVMSClient.exe", "VMSClient.exe", "Client\\Client.exe", "Client.exe", "BritonVMS.exe", "BRVMS.exe", "BRVMSClient.exe"]
    },
    "KDT VMS": {
        "keyword": "kdt",
        "executables": ["Kdt Client.exe", "VMSClient.exe", "Client\\Client.exe", "Client.exe", "KDT_VMS.exe", "KDTClientApp.exe", "SecurityVMS.exe"]
    },
    "SmartPSS": {
        "keyword": "smartpss",
        "executables": ["SmartPSS.exe", "SmartPSS Client.exe", "SmartPSSClien.exe", "Configtool.exe", "PMS.exe"] 
    },
    "EZStation Uniview": {  # اصلاح شده: Uniaview -> Uniview
        "keyword": "ezstation uniview",  # اصلاح شده
        "executables": ["EZStation.exe", "Uniview.exe", "UniviewClient.exe", "EZStationClient.exe", "UniviewService.exe", "EZStationService.exe"]  # اصلاح شده
    }
}

promotional_links_data = [
    {"text": "نرم افزار تایم لپس دوربین مداربسته", "url": "https://intellsoft.ir/product/timelapse-camera-recorder/"},
    {"text": "نرم افزار تبدیل فیلم دوربین مداربسته تایم لپس", "url": "https://intellsoft.ir/product/time-lapse-software-with-cctv-playback-film/"},
    {"text": "نرم افزار تبدیل عکس به فیلم تایم لپس", "url": "https://intellsoft.ir/product/time-lapse-photo-to-video/"}
]
current_link_index = 0

# --- توابع مربوط به بررسی آپدیت ---
def check_for_updates():
    """بررسی وجود نسخه جدید در GitHub"""
    try:
        # دریافت اطلاعات آخرین نسخه از گیت‌هاب
        with urllib.request.urlopen("https://api.github.com/repos/intellsoft/vms-software-reset-password/releases/latest") as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            # مقایسه نسخه‌ها
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                # نمایش پیام به کاربر
                update_frame.pack(pady=10, fill=tk.X)
                update_label.config(text=f"نسخه جدید {latest_version} موجود است!")
                
                # ذخیره URL دانلود برای استفاده در کلیک
                global download_url
                download_url = data['html_url']
    except Exception as e:
        # در صورت خطا (مثلاً عدم اتصال اینترنت) چیزی نمایش نمی‌دهیم
        pass

def download_update(event):
    """باز کردن مرورگر برای دانلود نسخه جدید"""
    webbrowser.open(download_url)

# --- توابع مربوط به ویرایش فایل KDT ---
def process_kdt_config_file(kdt_installation_path):
    """
    فایل config.ini را در مسیر نصب KDT VMS پیدا کرده و مقدار pwd را ویرایش می‌کند.
    """
    config_file_name = "config.ini"
    
    possible_config_paths = [
        os.path.join(kdt_installation_path, config_file_name),
        os.path.join(kdt_installation_path, "Client", config_file_name),
        os.path.join(kdt_installation_path, "conf", config_file_name),
        os.path.join(kdt_installation_path, "Config", config_file_name)
    ]

    found_config_path = None
    for p in possible_config_paths:
        if os.path.exists(p) and os.path.isfile(p):
            found_config_path = p
            break

    if not found_config_path:
        result_label.config(text=f"فایل {config_file_name} برای KDT VMS پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    new_pwd_value = "3A779DE4EA0B966B5D8EF767EFAFCC20"
    
    try:
        lines = []
        with open(found_config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        with open(found_config_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().lower().startswith("pwd="):
                    f.write(f"pwd={new_pwd_value}\n")
                    modified = True
                else:
                    f.write(line)
            
            if not modified:
                f.write(f"\npwd={new_pwd_value}\n")
                modified = True
        
        if modified:
            result_label.config(text="رمز عبور نرم افزار KDT VMS به 123456 تغییر یافت.")
        else:
            result_label.config(text=f"ویرایش KDT VMS ناموفق بود.")

    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل KDT VMS: {e}")
    
    # دکمه‌ها را دوباره فعال کن
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به SmartPSS ---
def process_smartpss_config_files(smartpss_installation_path):
    """
    فایل‌های conf.xml و conf.xml.usertmp را در مسیرهای مشخص شده SmartPSS حذف می‌کند.
    قبل از حذف، تلاش می‌کند پروسه‌های مربوط به SmartPSS را ببندد.
    """
    files_to_delete = ["conf.xml", "conf.xml.usertmp"]
    
    # Process names that might hold the file
    smartpss_process_names = [exe.lower() for exe in software_configs["SmartPSS"]["executables"]]
    
    killed_processes = []
    # Attempt to terminate SmartPSS processes
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in smartpss_process_names:
                # Check if the process executable is within the installation path
                # Use smartpss_installation_path for checking if process belongs to this installation
                if proc.info['exe'] and (smartpss_installation_path.lower() in proc.info['exe'].lower() or \
                                         r"c:\users\public\smartpss".lower() in proc.info['exe'].lower()): # Check both paths
                    result_label.config(text=f"در حال بستن پروسه: {proc.info['name']} (PID: {proc.info['pid']})...")
                    proc.terminate() # or proc.kill() for more aggressive termination
                    proc.wait(timeout=5) # Wait for the process to terminate
                    killed_processes.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            result_label.config(text=f"خطا در بستن پروسه {proc.info['name']}: {e}")

    if killed_processes:
        result_label.config(text=f"پروسه‌های زیر بسته شدند: {', '.join(killed_processes)}\nدر حال حذف فایل‌ها...")
    else:
        result_label.config(text="پروسه‌ای از SmartPSS در حال اجرا یافت نشد.\nدر حال حذف فایل‌ها...")

    base_deleted = False
    temp_deleted = False

    # List of directories where SmartPSS config files might reside
    # Including the user-selected path and the C:\Users\Public\SmartPSS path
    search_base_dirs = [
        smartpss_installation_path,
        r"C:\Users\Public\SmartPSS"
    ]
    
    # Possible subdirectories within each base directory where config files might be
    sub_dirs = ["", "Config", "General", os.path.join("UserData", "Config")]

    for file_name in files_to_delete:
        found_and_deleted = False
        for base_dir in search_base_dirs:
            for sub_dir in sub_dirs:
                file_path = os.path.join(base_dir, sub_dir, file_name)
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        if file_name == "conf.xml":
                            base_deleted = True
                        elif file_name == "conf.xml.usertmp":
                            temp_deleted = True
                        found_and_deleted = True
                        # No need to check other paths for this file once it's found and deleted
                        break 
                    except PermissionError:
                        result_label.config(text=f"خطای عدم دسترسی در حذف {file_name} از {file_path} برای SmartPSS: لطفاً برنامه را با دسترسی مدیر (Run as administrator) اجرا کنید و مطمئن شوید هیچ برنامه دیگری از این فایل استفاده نمی‌کند.")
                        select_path_button.config(state="enabled")
                        combo_box.config(state="readonly")
                        return # Stop if permission error occurs
                    except Exception as e:
                        result_label.config(text=f"خطا در حذف {file_name} از {file_path} برای SmartPSS: {e}")
                        select_path_button.config(state="enabled")
                        combo_box.config(state="readonly")
                        return # Stop if other error occurs
            if found_and_deleted:
                break # Break from base_dir loop if file was found and deleted

    if base_deleted or temp_deleted:
        result_label.config(text="رمز عبور نرم افزار SmartPSS ریست شد.")
    else:
        result_label.config(text="فایل‌های conf.xml یا conf.xml.usertmp برای SmartPSS در مسیرهای مشخص شده پیدا نشدند.")

    # دکمه‌ها را دوباره فعال کن
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به iVMS 4200 Lite و iVMS 4200 version 2 ---
def process_ivms_config(ivms_installation_path, software_name):
    """
    فایل 'system' را در مسیر نصب iVMS 4200 Lite یا iVMS 4200 version 2 حذف می‌کند.
    قبل از حذف، تلاش می‌کند پروسه‌های مربوطه را ببندد.
    """
    file_to_delete = "system"
    
    # Process names that might hold the file
    # Use the executables list from the software_configs for the given software_name
    ivms_process_names = [exe.lower() for exe in software_configs[software_name]["executables"]]
    
    killed_processes = []
    # Attempt to terminate iVMS processes
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ivms_process_names:
                # Check if the process executable is within the installation path
                if proc.info['exe'] and ivms_installation_path.lower() in proc.info['exe'].lower():
                    result_label.config(text=f"در حال بستن پروسه: {proc.info['name']} (PID: {proc.info['pid']})...")
                    proc.terminate() # or proc.kill() for more aggressive termination
                    proc.wait(timeout=5) # Wait for the process to terminate
                    killed_processes.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            result_label.config(text=f"خطا در بستن پروسه {proc.info['name']}: {e}")

    if killed_processes:
        result_label.config(text=f"پروسه‌های زیر بسته شدند: {', '.join(killed_processes)}\nدر حال حذف فایل...")
    else:
        result_label.config(text=f"پروسه‌ای از {software_name} در حال اجرا یافت نشد.\nدر حال حذف فایل...")

    possible_file_paths = [
        os.path.join(ivms_installation_path, file_to_delete),
        os.path.join(ivms_installation_path, "UserData", file_to_delete),
        os.path.join(ivms_installation_path, "data", file_to_delete),
        os.path.join(ivms_installation_path, "Config", file_to_delete)
    ]

    found_file_path = None
    for p in possible_file_paths:
        if os.path.exists(p) and os.path.isfile(p):
            found_file_path = p
            break

    if not found_file_path:
        result_label.config(text=f"فایل 'system' برای {software_name} پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return
    
    try:
        os.remove(found_file_path)
        result_label.config(text="رمز نرم افزار حذف شد، نرم افزار را دوباره اجرا کنید.")
    except PermissionError:
        result_label.config(text="خطای عدم دسترسی: لطفاً برنامه را با دسترسی مدیر (Run as administrator) اجرا کنید و مطمئن شوید هیچ برنامه دیگری از این فایل استفاده نمی‌کند.")
    except Exception as e:
        result_label.config(text=f"خطا در حذف فایل 'system' برای {software_name}: {e}")

    # دکمه‌ها را دوباره فعال کن
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به Briton VMS ---
def process_briton_config_file(briton_installation_path):
    """
    فایل users.xml را در مسیر نصب Briton VMS پیدا کرده و رمز عبور admin را تغییر می‌دهد.
    """
    config_file_name = "users.xml"
    
    # Path to xml folder, assuming it's directly under installation path
    xml_folder_path = os.path.join(briton_installation_path, "xml")
    full_config_path = os.path.join(xml_folder_path, config_file_name)

    if not os.path.exists(full_config_path) or not os.path.isfile(full_config_path):
        result_label.config(text=f"فایل {config_file_name} در مسیر {xml_folder_path} برای Briton VMS پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # The exact content to replace with (given by user for an empty password or default hash)
    # Note: The provided replacement block has a specific hash. This usually means a known default/empty password.
    new_users_block = """<USERS>
            <USER name="admin" password="76E0117E3E1D332ECEB2F466D2CE646D" group="administrator" describe="" stop="0" lock="0" />
        </USERS>"""
    
    try:
        with open(full_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the start and end of the existing <USERS> block
        start_tag = "<USERS>"
        end_tag = "</USERS>"
        
        start_index = content.find(start_tag)
        end_index = content.find(end_tag, start_index)

        if start_index != -1 and end_index != -1:
            # Replace the entire block
            # Add len(end_tag) to include the closing tag in the replacement span
            new_content = content[:start_index] + new_users_block + content[end_index + len(end_tag):]
            
            with open(full_config_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            result_label.config(text="رمز نرم افزار Briton VMS خالی شد.")
        else:
            result_label.config(text=f"بلاک <USERS> در فایل {config_file_name} برای Briton VMS پیدا نشد. ویرایش انجام نشد.")

    except PermissionError:
        result_label.config(text="خطای عدم دسترسی: لطفاً برنامه را با دسترسی مدیر (Run as administrator) اجرا کنید تا Briton VMS ویرایش شود.")
    except Exception as e:
        result_label.config(text=f"خطا در ویرایش فایل Briton VMS: {e}")
    
    # دکمه‌ها را دوباره فعال کن
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع مربوط به EZStation Uniview ---
def process_ezstation_uniview(ez_installation_path):  # اصلاح شده: uniaview -> uniview
    """
    فایل دیتابیس ezsv*.db را در مسیر نصب EZStation Uniview پیدا کرده
    و رمز عبور کاربر admin را تغییر می‌دهد.
    """
    # Process names that might hold the file
    ez_process_names = [exe.lower() for exe in software_configs["EZStation Uniview"]["executables"]]  # اصلاح شده
    
    killed_processes = []
    # Attempt to terminate EZStation processes
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ez_process_names:
                # Check if the process executable is within the installation path
                if proc.info['exe'] and ez_installation_path.lower() in proc.info['exe'].lower():
                    result_label.config(text=f"در حال بستن پروسه: {proc.info['name']} (PID: {proc.info['pid']})...")
                    proc.terminate() # or proc.kill() for more aggressive termination
                    proc.wait(timeout=5) # Wait for the process to terminate
                    killed_processes.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            result_label.config(text=f"خطا در بستن پروسه {proc.info['name']}: {e}")

    if killed_processes:
        result_label.config(text=f"پروسه‌های زیر بسته شدند: {', '.join(killed_processes)}\nدر حال جستجوی دیتابیس...")
    else:
        result_label.config(text=f"پروسه‌ای از EZStation Uniview در حال اجرا یافت نشد.\nدر حال جستجوی دیتابیس...")  # اصلاح شده

    # جستجوی فایل‌های دیتابیس با الگوی ezsv*.db
    db_files = glob.glob(os.path.join(ez_installation_path, 'ezsv*.db'))
    
    if not db_files:
        result_label.config(text="هیچ فایل دیتابیس ezsv*.db پیدا نشد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")
        return

    # انتخاب اولین فایل دیتابیس پیدا شده
    db_path = db_files[0]
    result_label.config(text=f"پیدا کردن دیتابیس: {db_path}\nدر حال ویرایش...")

    try:
        # اتصال به دیتابیس SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # ویرایش رمز عبور کاربر admin
        cursor.execute("UPDATE tbl_user SET fl_user_password = ? WHERE fl_user_name = ?", 
                      ("?XND?NN&?lN0", "admin"))
        
        # بررسی تعداد ردیف‌های تاثیر گرفته
        if cursor.rowcount > 0:
            conn.commit()
            result_label.config(text="رمز ورود به نرم افزار 123456 با کاربر admin است")
        else:
            result_label.config(text="کاربر admin در دیتابیس پیدا نشد")
        
        conn.close()
        
    except sqlite3.Error as e:
        result_label.config(text=f"خطا در ویرایش دیتابیس: {str(e)}\nنسخه نرم افزار شما پشتیبانی نمی شود. منتظر نسخه های بعدی باشید.")
    except Exception as e:
        result_label.config(text=f"خطای غیرمنتظره: {str(e)}")
    
    # دکمه‌ها را دوباره فعال کن
    select_path_button.config(state="enabled")
    combo_box.config(state="readonly")

# --- توابع GUI ---
def select_installation_path_and_process():
    """
    کادر محاوره برای انتخاب دستی مسیر نصب نرم‌افزار را نمایش می‌دهد
    و سپس بر اساس نرم‌افزار انتخاب شده، عملیات مربوطه را انجام می‌دهد.
    """
    selected_software_name = combo_box.get()
    
    if not selected_software_name:
        result_label.config(text="لطفاً یک نرم‌افزار را انتخاب کنید.")
        return

    # غیرفعال کردن دکمه و کامبوباکس هنگام انتخاب مسیر
    select_path_button.config(state="disabled")
    combo_box.config(state="disabled")
    result_label.config(text="لطفاً پوشه نصب را انتخاب کنید...")

    initial_dir = os.path.expanduser("~") 
    
    folder_path = filedialog.askdirectory(initialdir=initial_dir, 
                                          title=f"لطفاً پوشه نصب {selected_software_name} را انتخاب کنید")
    
    if folder_path:
        result_label.config(text=f"مسیر انتخاب شده: {folder_path}\nدر حال پردازش...")
        
        # اجرای عملیات مربوط به نرم‌افزار در یک ترد جداگانه
        if selected_software_name == "KDT VMS":
            process_thread = threading.Thread(target=process_kdt_config_file, args=(folder_path,), daemon=True)
        elif selected_software_name == "SmartPSS":
            # SmartPSS now also calls the common process termination logic
            process_thread = threading.Thread(target=process_smartpss_config_files, args=(folder_path,), daemon=True)
        elif selected_software_name == "iVMS 4200 Lite": 
            process_thread = threading.Thread(target=process_ivms_config, args=(folder_path, selected_software_name,), daemon=True)
        elif selected_software_name == "iVMS 4200 version 2": 
            # iVMS 4200 version 2 also uses the common iVMS processing logic
            process_thread = threading.Thread(target=process_ivms_config, args=(folder_path, selected_software_name,), daemon=True)
        elif selected_software_name == "Briton VMS": 
            process_thread = threading.Thread(target=process_briton_config_file, args=(folder_path,), daemon=True)
        elif selected_software_name == "EZStation Uniview":  # اصلاح شده: Uniaview -> Uniview
            process_thread = threading.Thread(target=process_ezstation_uniview, args=(folder_path,), daemon=True)  # اصلاح شده
        else:
            result_label.config(text=f"عملیاتی برای {selected_software_name} تعریف نشده است.")
            select_path_button.config(state="enabled")
            combo_box.config(state="readonly")
            return
        
        process_thread.start() # شروع ترد پردازش
    else:
        result_label.config(text="انتخاب مسیر لغو شد.")
        select_path_button.config(state="enabled")
        combo_box.config(state="readonly")

def rotate_links():
    global current_link_index
    link_info = promotional_links_data[current_link_index]
    
    # تغییر متن و لینک Label
    rotating_link_label.config(text=link_info["text"], cursor="hand2")
    rotating_link_label.bind("<Button-1>", lambda e: os.startfile(link_info["url"]))

    current_link_index = (current_link_index + 1) % len(promotional_links_data)
    root.after(3000, rotate_links) # هر 3 ثانیه یک بار چرخش می‌کند


# --- تنظیمات GUI ---
root = tk.Tk()
root.title("Reset VMS software password")
root.geometry("500x450") # افزایش ارتفاع برای نمایش پیام آپدیت
root.resizable(False, False)

# فریم برای نمایش پیام آپدیت
update_frame = ttk.Frame(root)
update_frame.pack(pady=5, fill=tk.X)
update_frame.pack_forget()  # ابتدا مخفی است

update_label = tk.Label(
    update_frame, 
    text="",
    fg="green",
    cursor="hand2",
    font=("B Nazanin", 10, "bold")
)
update_label.pack(pady=5)
update_label.bind("<Button-1>", download_update)

instruction_label = ttk.Label(root, text="نرم‌افزار مورد نظر را انتخاب کنید:")
instruction_label.pack(pady=10)

software_options = sorted(list(software_configs.keys()))
combo_box = ttk.Combobox(root, values=software_options, state="readonly", width=30)
combo_box.set(software_options[0] if software_options else "")
combo_box.pack(pady=5)

select_path_button = ttk.Button(root, text="انتخاب مسیر نصب و اجرا", command=select_installation_path_and_process)
select_path_button.pack(pady=10)

result_label = ttk.Label(root, text="پس از انتخاب نرم‌افزار، مسیر نصب را انتخاب کنید.", wraplength=450)
result_label.pack(pady=10)

# استفاده از Frame برای قرار دادن اطلاعات برنامه‌نویس و لینک‌ها در پایین پنجره
bottom_frame = ttk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10) # چسباندن به پایین پنجره و پر کردن عرض

developer_label = ttk.Label(bottom_frame, text="برنامه نویس : محمدعلی عباسپور (نرم افزار تخصصی دوربین مداربسته اینتل سافت)")
developer_label.pack(pady=(0,2)) # کمی فاصله از بالا

developer_link = tk.Label(bottom_frame, text="https://intellsoft.ir", fg="blue", cursor="hand2")
developer_link.pack(pady=(0,5))
developer_link.bind("<Button-1>", lambda e: os.startfile("https://intellsoft.ir"))


# Style for orange background
style = ttk.Style()
style.configure("Orange.TFrame", background="#FFA500") # نارنجی متوسط
style.configure("Orange.TLabel", background="#FFA500", foreground="white", font=("B Nazanin", 10, "bold")) # متن سفید و پررنگ

# Frame for rotating links
rotating_link_frame = ttk.Frame(bottom_frame, style="Orange.TFrame") # قرار دادن در bottom_frame
rotating_link_frame.pack(fill=tk.X, pady=(5,0)) # پر کردن عرض و کمی فاصله از بالا

rotating_link_label = tk.Label(rotating_link_frame, text="", bg="#FFA500", fg="white", cursor="hand2", font=("B Nazanin", 10, "bold"))
rotating_link_label.pack(pady=5)

# شروع چرخش
rotate_links()

# شروع بررسی آپدیت در پس‌زمینه
update_thread = threading.Thread(target=check_for_updates, daemon=True)
update_thread.start()

root.mainloop()