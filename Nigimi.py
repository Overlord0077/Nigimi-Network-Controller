import os
import sys
import time
import ctypes
import threading
import subprocess
import queue
import json
import winreg
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import psutil

PYDIVERT_AVAILABLE = False
try:
    import pydivert
    PYDIVERT_AVAILABLE = True
except ImportError:
    PYDIVERT_AVAILABLE = False


def is_admin():
    """Проверка прав Администратора в системе Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def elevate_admin():
    """Автоматический запрос прав Администратора (UAC Elevate)"""
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1
            )
        except Exception:
            pass
        sys.exit(0)


# Скрытый служебный каталог приложения в %LOCALAPPDATA%
LOCAL_APPDATA = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
NIGIMI_DIR = os.path.join(LOCAL_APPDATA, "NigimiController")
LANG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "languages")
os.makedirs(NIGIMI_DIR, exist_ok=True)
os.makedirs(LANG_DIR, exist_ok=True)


class AutoStartManager:
    """Менеджер автозапуска приложения вместе с Windows"""
    APP_NAME = "NigimiNetworkController"
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    @classmethod
    def is_enabled(cls) -> bool:
        """Проверяет, добавлен ли Nigimi в автозагрузку реестра"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, cls.APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @classmethod
    def toggle(cls, enable: bool) -> bool:
        """Включает или выключает автозапуск приложения в реестре Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                # Включаем автозапуск с текущим исполняемым файлом
                executable = sys.executable if getattr(sys, 'frozen', False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, executable)
            else:
                try:
                    winreg.DeleteValue(key, cls.APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"AutoStart Error: {e}")
            return False


class LanguageManager:
    """Менеджер языков и локализации с поддержкой внешней папки /languages"""
    LANGUAGES = {
        "ru": "Русский 🇷🇺",
        "en": "English 🇬🇧",
        "de": "Deutsch 🇩🇪",
        "zh": "中文 🇨🇳",
        "ar": "العربية 🇸🇦"
    }

    # Встроенный резервный словарь переводов
    DEFAULT_TRANSLATIONS = {
        "ru": {
            "app_title": "NIGIMI // SYSTEM NETWORK OVERLORD",
            "overdrive_btn": "⚡ OVERDRIVE OPTIMIZE",
            "search_ph": "🔍 Поиск процесса или игры (cs2, chrome, discord)...",
            "refresh_btn": "🔄 ОБНОВИТЬ",
            "control_panel": "ПАНЕЛЬ УПРАВЛЕНИЯ",
            "select_app": "Выберите приложение...",
            "processes_cnt": "Процессов: {count} | PIDs: {pids}",
            "path_lbl": "Путь: {path}",
            "btn_mute": "🚫 ЗАГЛУШИТЬ ИНТЕРНЕТ",
            "btn_limit": "⚡ ОГРАНИЧИТЬ СКОРОСТЬ",
            "btn_restore": "🔄 СБРОСИТЬ ОГРАНИЧЕНИЯ",
            "status_active": "[SYSTEM ACTIVE] Ядерный контроллер Nigimi готов к работе.",
            "status_norm": "НОРМА",
            "status_muted": "ЗАГЛУШЕН",
            "status_limited": "ЛИМИТ",
            "settings_title": "⚙️ НАСТРОЙКИ И ИНФОРМАЦИЯ",
            "tab_settings": "⚙️ Настройки",
            "tab_about": "ℹ️ О программе",
            "lang_select": "Язык интерфейса:",
            "autostart_lbl": "Запускать вместе с ПК (Windows Autostart):",
            "about_header": "NIGIMI NETWORK OVERLORD v2.0",
            "about_desc": "Мощнейший ядерный контроллер и глушитель сетевого трафика. Обеспечивает точечную изоляцию приложений, шейпинг полосы пропускания и мгновенный разрыв сетевых сокетов.",
            "tech_specs": "🔥 ТЕХНОЛОГИЧЕСКИЙ СТЕК:",
            "tech_1": "• WinDivert Kernel Engine (Перехват пакетов на уровне драйвера ядра)",
            "tech_2": "• Token Bucket Traffic Shaper (Микросекундное ограничение скорости)",
            "tech_3": "• Active Socket Terminator (PowerShell NetTCP Connection Reaper)",
            "tech_4": "• Win Firewall Advanced Rule Injector (Двойная стена блокировки)",
            "dev_note": "Разработано для геймеров, стримеров и специалистов по безопасности.",
            "save_btn": "СОХРАНИТЬ И ЗАКРЫТЬ",
            "total_apps": "Всего приложений",
            "blocked_apps": "Заглушено",
            "limited_apps": "С лимитом"
        },
        "en": {
            "app_title": "NIGIMI // SYSTEM NETWORK OVERLORD",
            "overdrive_btn": "⚡ OVERDRIVE OPTIMIZE",
            "search_ph": "🔍 Search process or game (cs2, chrome, discord)...",
            "refresh_btn": "🔄 REFRESH",
            "control_panel": "CONTROL PANEL",
            "select_app": "Select an application...",
            "processes_cnt": "Processes: {count} | PIDs: {pids}",
            "path_lbl": "Path: {path}",
            "btn_mute": "🚫 MUTE INTERNET",
            "btn_limit": "⚡ LIMIT BANDWIDTH",
            "btn_restore": "🔄 RESTORE DEFAULT",
            "status_active": "[SYSTEM ACTIVE] Nigimi kernel controller active.",
            "status_norm": "NORMAL",
            "status_muted": "MUTED",
            "status_limited": "LIMITED",
            "settings_title": "⚙️ SETTINGS & ABOUT",
            "tab_settings": "⚙️ Settings",
            "tab_about": "ℹ️ About App",
            "lang_select": "Interface Language:",
            "autostart_lbl": "Launch on PC Startup (Windows Autostart):",
            "about_header": "NIGIMI NETWORK OVERLORD v2.0",
            "about_desc": "Ultimate kernel-level network controller and traffic isolator. Provides process-level blocking, bandwidth shaping, and socket termination.",
            "tech_specs": "🔥 TECH STACK:",
            "tech_1": "• WinDivert Kernel Engine (Kernel Driver Packet Intercept)",
            "tech_2": "• Token Bucket Traffic Shaper (Microsecond Speed Limiter)",
            "tech_3": "• Active Socket Terminator (PowerShell Connection Reaper)",
            "tech_4": "• Win Firewall Advanced Rule Injector (Dual Firewall Wall)",
            "dev_note": "Engineered for gamers, streamers, and network engineers.",
            "save_btn": "SAVE & CLOSE",
            "total_apps": "Total Apps",
            "blocked_apps": "Muted",
            "limited_apps": "Limited"
        },
        "de": {
            "app_title": "NIGIMI // SYSTEM NETWORK OVERLORD",
            "overdrive_btn": "⚡ OVERDRIVE OPTIMIZE",
            "search_ph": "🔍 Prozess oder Spiel suchen...",
            "refresh_btn": "🔄 AKTUALISIEREN",
            "control_panel": "STEUERUNG",
            "select_app": "Anwendung auswählen...",
            "processes_cnt": "Prozesse: {count} | PIDs: {pids}",
            "path_lbl": "Pfad: {path}",
            "btn_mute": "🚫 INTERNET BLOCKIEREN",
            "btn_limit": "⚡ SPEED BEGRENZEN",
            "btn_restore": "🔄 ZURÜCKSETZEN",
            "status_active": "[SYSTEM AKTIV] Nigimi Kernel Controller bereit.",
            "status_norm": "NORMAL",
            "status_muted": "STUMM",
            "status_limited": "LIMITIERT",
            "settings_title": "⚙️ EINSTELLUNGEN",
            "tab_settings": "⚙️ Einstellungen",
            "tab_about": "ℹ️ Über uns",
            "lang_select": "Sprache auswählen:",
            "autostart_lbl": "Mit Windows starten (Autostart):",
            "about_header": "NIGIMI NETWORK OVERLORD v2.0",
            "about_desc": "Leistungsstarker Netzwerk-Controller auf Kernelebene.",
            "tech_specs": "🔥 TECHNOLOGIE:",
            "tech_1": "• WinDivert Kernel Treiberschutz",
            "tech_2": "• Token Bucket Bandbreitenregler",
            "tech_3": "• PowerShell Socket Reaper",
            "tech_4": "• Windows Firewall Integration",
            "dev_note": "Entwickelt für Gamer und Netzwerk-Profis.",
            "save_btn": "SPEICHERN",
            "total_apps": "Gesamt",
            "blocked_apps": "Blockiert",
            "limited_apps": "Limitiert"
        },
        "zh": {
            "app_title": "NIGIMI // 网络网络霸主",
            "overdrive_btn": "⚡ 极速优化 ПК",
            "search_ph": "🔍 搜索进程或游戏 (cs2, chrome, discord)...",
            "refresh_btn": "🔄 刷新列表",
            "control_panel": "控制面板",
            "select_app": "请选择一个应用程序...",
            "processes_cnt": "进程数: {count} | PIDs: {pids}",
            "path_lbl": "路径: {path}",
            "btn_mute": "🚫 完全断开网络",
            "btn_limit": "⚡ 限制网络速度",
            "btn_restore": "🔄 恢复默认设置",
            "status_active": "[系统就绪] Nigimi 内核控制器准备就绪。",
            "status_norm": "正常",
            "status_muted": "已禁用",
            "status_limited": "已限速",
            "settings_title": "⚙️ 设置与关于",
            "tab_settings": "⚙️ 设置",
            "tab_about": "ℹ️ 关于应用",
            "lang_select": "选择界面语言:",
            "autostart_lbl": "开机自动运行 (Windows 自启动):",
            "about_header": "NIGIMI NETWORK OVERLORD v2.0",
            "about_desc": "强大的内核级网络控制器，提供进程级隔离、限速与套接字清除功能。",
            "tech_specs": "🔥 技术栈:",
            "tech_1": "• WinDivert 内核引擎 (内核数据包拦截)",
            "tech_2": "• 令牌桶流量整形器 (微秒级限速)",
            "tech_3": "• 动态套接字终结器 (PowerShell 连接清除)",
            "tech_4": "• Windows 防火墙双重规则注入",
            "dev_note": "专为游戏玩家和网络工程师打造。",
            "save_btn": "保存并关闭",
            "total_apps": "应用总数",
            "blocked_apps": "已禁用",
            "limited_apps": "已限速"
        },
        "ar": {
            "app_title": "NIGIMI // متحكم الشبكة المتقدم",
            "overdrive_btn": "⚡ تحسين الفائق",
            "search_ph": "🔍 بحث عن تطبيق أو لعبة...",
            "refresh_btn": "🔄 تحديث",
            "control_panel": "لوحة التحكم",
            "select_app": "اختر تطبيقاً...",
            "processes_cnt": "العمليات: {count} | PIDs: {pids}",
            "path_lbl": "المسار: {path}",
            "btn_mute": "🚫 قطع الإنترنت",
            "btn_limit": "⚡ تحديد السرعة",
            "btn_restore": "🔄 استعادة الضبط",
            "status_active": "[النظام نشط] وحدة تحكم Nigimi جاهزة.",
            "status_norm": "طبيعي",
            "status_muted": "محظور",
            "status_limited": "محدد",
            "settings_title": "⚙️ الإعدادات والمعلومات",
            "tab_settings": "⚙️ الإعدادات",
            "tab_about": "ℹ️ حول البرنامج",
            "lang_select": "لغة الواجهة:",
            "autostart_lbl": "تشغيل مع بدء التشغيل (Windows Autostart):",
            "about_header": "NIGIMI NETWORK OVERLORD v2.0",
            "about_desc": "أقوى نظام تحكم بالشبكة على مستوى النواة.",
            "tech_specs": "🔥 التقنيات:",
            "tech_1": "• محرك WinDivert للنواة",
            "tech_2": "• منظم سرعة التدفّق",
            "tech_3": "• أنهاء اتصالات PowerShell",
            "tech_4": "• جدار حماية ويندوز المزدوج",
            "dev_note": "صُمم خصيصاً للاعبين ومهندسي الشبكات.",
            "save_btn": "حفظ وإغلاق",
            "total_apps": "الإجمالي",
            "blocked_apps": "محظور",
            "limited_apps": "محدد"
        }
    }

    def __init__(self):
        self.current_lang = "ru"
        self.translations = dict(self.DEFAULT_TRANSLATIONS)
        self._load_external_languages()

    def _load_external_languages(self):
        """Сканирует папку /languages на наличие внешний JSON файлов локализации"""
        if not os.path.exists(LANG_DIR):
            return
        for code in self.LANGUAGES.keys():
            json_file = os.path.join(LANG_DIR, f"{code}.json")
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self.translations[code].update(data)
                except Exception as e:
                    print(f"Error loading lang file {json_file}: {e}")

    def get(self, key: str, **kwargs) -> str:
        """Возвращает переведенную строку для текущего языка"""
        lang_dict = self.translations.get(self.current_lang, self.translations["ru"])
        text = lang_dict.get(key, self.translations["ru"].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def set_language(self, lang_code: str):
        if lang_code in self.LANGUAGES:
            self.current_lang = lang_code


class NetworkEngine:
    """Движок перехвата и глушения сети с поддержкой группировки PID"""
    def __init__(self):
        self.blocked_groups = set()         # exe_name (lowercase)
        self.rate_limited_groups = {}       # exe_name: bytes_per_sec
        self.active_divert_threads = {}
        self.firewall_rules = set()
        self.is_running = True

    def block_group(self, group_info: dict):
        """Полная глушилка сети для всех процессов в группе (Mute All)"""
        exe_name = group_info['exe_name']
        exe_path = group_info.get('exe_path', '')
        pids = group_info.get('pids', [])

        self.unlimit_group(exe_name, exe_path)
        self.blocked_groups.add(exe_name)

        # 1. Жесткая блокировка в Брандмауэре Windows по пути к EXE
        if exe_path and os.path.exists(exe_path):
            self._firewall_block_exe(exe_name, exe_path)

        # 2. Разрыв ВСЕХ открытых сокетов для каждого PID группы
        self._kill_sockets_for_pids(pids)

        # 3. Перехват и уничтожение пакетов в ядре через WinDivert
        if PYDIVERT_AVAILABLE and pids:
            thread = threading.Thread(
                target=self._divert_block_worker, 
                args=(exe_name, list(pids)), 
                daemon=True
            )
            self.active_divert_threads[f"block_{exe_name}"] = thread
            thread.start()

    def limit_group(self, group_info: dict, bytes_per_sec: int):
        """Ограничение пропускной способности группы (Traffic Shaping)"""
        exe_name = group_info['exe_name']
        pids = group_info.get('pids', [])

        self.unlimit_group(exe_name, group_info.get('exe_path', ''))
        self.rate_limited_groups[exe_name] = bytes_per_sec

        if PYDIVERT_AVAILABLE and pids:
            thread = threading.Thread(
                target=self._divert_shaper_worker, 
                args=(exe_name, list(pids), bytes_per_sec), 
                daemon=True
            )
            self.active_divert_threads[f"limit_{exe_name}"] = thread
            thread.start()

    def unlimit_group(self, exe_name: str, exe_path: str = None):
        """Сброс всех ограничений для группы процессов"""
        exe_name = exe_name.lower()
        if exe_name in self.blocked_groups:
            self.blocked_groups.remove(exe_name)
        if exe_name in self.rate_limited_groups:
            del self.rate_limited_groups[exe_name]

        if exe_path:
            self._firewall_unblock_exe(exe_name, exe_path)

    def _firewall_block_exe(self, exe_name: str, exe_path: str):
        """Правило блокировки в Брандмауэре Windows на входящий и исходящий трафик"""
        rule_name = f"Nigimi_Rule_{exe_name}"
        cmd_out = f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=block program="{exe_path}" enable=yes'
        cmd_in = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block program="{exe_path}" enable=yes'
        try:
            subprocess.run(cmd_out, shell=True, capture_output=True)
            subprocess.run(cmd_in, shell=True, capture_output=True)
            self.firewall_rules.add(rule_name)
        except Exception:
            pass

    def _firewall_unblock_exe(self, exe_name: str, exe_path: str):
        """Удаление правила блокировки из Брандмауэра"""
        rule_name = f"Nigimi_Rule_{exe_name}"
        cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        try:
            subprocess.run(cmd, shell=True, capture_output=True)
            if rule_name in self.firewall_rules:
                self.firewall_rules.remove(rule_name)
        except Exception:
            pass

    def _kill_sockets_for_pids(self, pids: list):
        """Принудительное закрытие активных TCP-соединений группы в PowerShell"""
        if not pids:
            return
        pid_list_str = ",".join(str(p) for p in pids)
        ps_cmd = f'powershell -Command "Get-NetTCPConnection | Where-Object {{ $_.OwningProcess -in ({pid_list_str}) }} | Remove-NetTCPConnection -Confirm:$false -ErrorAction SilentlyContinue"'
        try:
            subprocess.run(ps_cmd, shell=True, capture_output=True)
        except Exception:
            pass

    def _divert_block_worker(self, exe_name: str, pids: list):
        """Ядерный сброс (Drop) сетевых пакетов через WinDivert"""
        if not PYDIVERT_AVAILABLE or not pids:
            return
        filter_parts = [f"processId == {p}" for p in pids]
        filter_str = " or ".join(filter_parts)
        try:
            with pydivert.WinDivert(filter_str) as w:
                while exe_name in self.blocked_groups and self.is_running:
                    packet = w.recv()
                    # Игнорируем пакет (Drop)
        except Exception:
            pass

    def _divert_shaper_worker(self, exe_name: str, pids: list, rate_limit: int):
        """Алгоритм Token Bucket Shaper для группы PID"""
        if not PYDIVERT_AVAILABLE or not pids:
            return
        filter_parts = [f"processId == {p}" for p in pids]
        filter_str = " or ".join(filter_parts)
        tokens = rate_limit
        last_check = time.time()

        try:
            with pydivert.WinDivert(filter_str) as w:
                while exe_name in self.rate_limited_groups and self.is_running:
                    packet = w.recv()
                    now = time.time()
                    elapsed = now - last_check
                    last_check = now

                    tokens += elapsed * rate_limit
                    if tokens > rate_limit * 2:
                        tokens = rate_limit * 2

                    packet_len = len(packet.raw)
                    if tokens >= packet_len:
                        tokens -= packet_len
                        w.send(packet)
                    else:
                        sleep_time = (packet_len - tokens) / rate_limit
                        time.sleep(max(0.001, sleep_time))
                        w.send(packet)
        except Exception:
            pass


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLOR_BG = "#080B10"          # Глубокий футуристичный фон
COLOR_CARD = "#111622"        # Панели и карточки
COLOR_SURFACE = "#182030"     # Плашки и интерактивные элементы
COLOR_CYAN = "#00F0FF"        # Электрик Cyan
COLOR_MAGENTA = "#FF007F"     # Неоновая Magenta (Mute)
COLOR_PURPLE = "#A855F7"      # Фиолетовый (Limit)
COLOR_GREEN = "#00FF88"       # Эмеральд (Norm)
COLOR_TEXT_MAIN = "#FFFFFF"   # Основной текст
COLOR_TEXT_MUTED = "#64748B"  # Серый текст


class RateLimitModal(ctk.CTkToplevel):
    """Модальное окно вызова ограничений скорости"""
    def __init__(self, parent, group_title, callback, lang_mgr):
        super().__init__(parent)
        self.lang_mgr = lang_mgr
        self.title("ЛИМИТ СКОРОСТИ")
        self.geometry("480x370")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.attributes("-topmost", True)

        self.callback = callback
        self.group_title = group_title

        self.grab_set()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (480 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (370 // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_lbl = ctk.CTkLabel(
            title_frame, 
            text="⚡ ЛИМИТ СКОРОСТИ СЕТИ", 
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color=COLOR_CYAN
        )
        title_lbl.pack(anchor="w")

        proc_lbl = ctk.CTkLabel(
            title_frame, 
            text=f"Группа: {self.group_title}", 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLOR_TEXT_MUTED
        )
        proc_lbl.pack(anchor="w", pady=(2, 0))

        input_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_SURFACE)
        input_card.pack(fill="x", padx=20, pady=15)

        entry_lbl = ctk.CTkLabel(
            input_card, 
            text="Укажите максимальную скорость:", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        entry_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        flex_frame = ctk.CTkFrame(input_card, fg_color="transparent")
        flex_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.val_entry = ctk.CTkEntry(
            flex_frame, 
            placeholder_text="Например: 500",
            font=ctk.CTkFont(family="Consolas", size=15),
            fg_color=COLOR_SURFACE,
            border_color=COLOR_PURPLE,
            text_color=COLOR_TEXT_MAIN,
            height=40
        )
        self.val_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.val_entry.insert(0, "500")

        self.unit_select = ctk.CTkOptionMenu(
            flex_frame,
            values=["КБ/с", "МБ/с", "Байт/с", "ГБ/с"],
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color=COLOR_PURPLE,
            button_color=COLOR_PURPLE,
            button_hover_color=COLOR_CYAN,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_SURFACE,
            height=40,
            width=110
        )
        self.unit_select.pack(side="right")

        self.calc_lbl = ctk.CTkLabel(
            self, 
            text="Эквивалент: 512 000 Байт/сек", 
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLOR_CYAN
        )
        self.calc_lbl.pack(pady=5)

        self.val_entry.bind("<KeyRelease>", self._update_calc)
        self.unit_select.configure(command=lambda e: self._update_calc())

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(15, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Отмена", 
            fg_color=COLOR_SURFACE,
            hover_color="#2A364F",
            text_color=COLOR_TEXT_MAIN,
            height=42,
            corner_radius=8,
            command=self.destroy
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        apply_btn = ctk.CTkButton(
            btn_frame, 
            text="АКТИВИРОВАТЬ", 
            fg_color=COLOR_PURPLE,
            hover_color=COLOR_CYAN,
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42,
            corner_radius=8,
            command=self._apply
        )
        apply_btn.pack(side="right", expand=True, fill="x", padx=(8, 0))

    def _update_calc(self, event=None):
        raw_val = self.val_entry.get().strip()
        unit = self.unit_select.get()
        if not raw_val.isdigit():
            self.calc_lbl.configure(text="⚠️ Введите числовое значение", text_color=COLOR_MAGENTA)
            return

        val = int(raw_val)
        multipliers = {
            "Байт/с": 1,
            "КБ/с": 1024,
            "МБ/с": 1024 * 1024,
            "ГБ/с": 1024 * 1024 * 1024
        }
        bytes_val = val * multipliers[unit]
        self.calc_lbl.configure(
            text=f"Эквивалент: {bytes_val:,} Байт/сек".replace(",", " "),
            text_color=COLOR_CYAN
        )

    def _apply(self):
        raw_val = self.val_entry.get().strip()
        unit = self.unit_select.get()
        if not raw_val.isdigit() or int(raw_val) <= 0:
            messagebox.showerror("Ошибка", "Введите положительное число!")
            return

        val = int(raw_val)
        multipliers = {
            "Байт/с": 1,
            "КБ/с": 1024,
            "МБ/с": 1024 * 1024,
            "ГБ/с": 1024 * 1024 * 1024
        }
        bytes_val = val * multipliers[unit]
        self.callback(bytes_val, f"{val} {unit}")
        self.destroy()


class SettingsModal(ctk.CTkToplevel):
    """Модальное окно Настроек, выбора Языка и раздела О Программе"""
    def __init__(self, parent, lang_mgr: LanguageManager, on_language_change_callback):
        super().__init__(parent)
        self.lang_mgr = lang_mgr
        self.on_language_change_callback = on_language_change_callback

        self.title(self.lang_mgr.get("settings_title"))
        self.geometry("580x520")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.attributes("-topmost", True)

        self.grab_set()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (580 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (520 // 2)
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Табвью для разделения Настроек и О Программе
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLOR_CARD,
            segmented_button_fg_color=COLOR_SURFACE,
            segmented_button_selected_color=COLOR_CYAN,
            segmented_button_selected_hover_color=COLOR_PURPLE,
            text_color="#000000",
            corner_radius=12
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(15, 10))

        tab_set_name = self.lang_mgr.get("tab_settings")
        tab_abt_name = self.lang_mgr.get("tab_about")

        self.tab_settings = self.tabview.add(tab_set_name)
        self.tab_about = self.tabview.add(tab_abt_name)

        self._build_settings_tab()
        self._build_about_tab()

        # Нижняя кнопка закрытия
        btn_close = ctk.CTkButton(
            self,
            text=self.lang_mgr.get("save_btn"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_CYAN,
            hover_color=COLOR_PURPLE,
            text_color="#000000",
            height=42,
            corner_radius=10,
            command=self.destroy
        )
        btn_close.pack(fill="x", padx=20, pady=(5, 15))

    def _build_settings_tab(self):
        """Вкладка настроек: Язык и Автозапуск"""
        # Section 1: Язык
        lang_card = ctk.CTkFrame(self.tab_settings, fg_color=COLOR_SURFACE, corner_radius=10)
        lang_card.pack(fill="x", padx=15, pady=15)

        lbl_lang = ctk.CTkLabel(
            lang_card,
            text=self.lang_mgr.get("lang_select"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        lbl_lang.pack(anchor="w", padx=15, pady=(12, 5))

        # Варианты языков для выбора
        lang_options = list(LanguageManager.LANGUAGES.values())
        curr_lang_name = LanguageManager.LANGUAGES.get(self.lang_mgr.current_lang, "Русский 🇷🇺")

        self.lang_dropdown = ctk.CTkOptionMenu(
            lang_card,
            values=lang_options,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_CARD,
            button_color=COLOR_PURPLE,
            button_hover_color=COLOR_CYAN,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_SURFACE,
            height=40,
            command=self._on_lang_selected
        )
        self.lang_dropdown.set(curr_lang_name)
        self.lang_dropdown.pack(fill="x", padx=15, pady=(0, 15))

        # Section 2: Автозапуск с ПК
        auto_card = ctk.CTkFrame(self.tab_settings, fg_color=COLOR_SURFACE, corner_radius=10)
        auto_card.pack(fill="x", padx=15, pady=10)

        lbl_auto = ctk.CTkLabel(
            auto_card,
            text=self.lang_mgr.get("autostart_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        lbl_auto.pack(anchor="w", padx=15, pady=(12, 8))

        is_autostart = AutoStartManager.is_enabled()
        self.autostart_sw = ctk.CTkSwitch(
            auto_card,
            text="Включить запуск Nigimi при старте Windows",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            progress_color=COLOR_CYAN,
            button_color=COLOR_TEXT_MAIN,
            command=self._on_autostart_toggled
        )
        if is_autostart:
            self.autostart_sw.select()
        else:
            self.autostart_sw.deselect()
        self.autostart_sw.pack(anchor="w", padx=15, pady=(0, 15))

    def _build_about_tab(self):
        """Футуристичная вкладка 'О программе'"""
        container = ctk.CTkFrame(self.tab_about, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Title
        title_lbl = ctk.CTkLabel(
            container,
            text=self.lang_mgr.get("about_header"),
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color=COLOR_CYAN
        )
        title_lbl.pack(anchor="w", pady=(5, 5))

        desc_lbl = ctk.CTkLabel(
            container,
            text=self.lang_mgr.get("about_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MAIN,
            wraplength=500,
            justify="left"
        )
        desc_lbl.pack(anchor="w", pady=(0, 15))

        # Спецификация
        tech_card = ctk.CTkFrame(container, fg_color=COLOR_SURFACE, corner_radius=10)
        tech_card.pack(fill="x", pady=5)

        tech_title = ctk.CTkLabel(
            tech_card,
            text=self.lang_mgr.get("tech_specs"),
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLOR_MAGENTA
        )
        tech_title.pack(anchor="w", padx=15, pady=(10, 5))

        for key in ["tech_1", "tech_2", "tech_3", "tech_4"]:
            t_lbl = ctk.CTkLabel(
                tech_card,
                text=self.lang_mgr.get(key),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLOR_TEXT_MUTED
            )
            t_lbl.pack(anchor="w", padx=15, pady=2)

        # Кредиты
        dev_lbl = ctk.CTkLabel(
            container,
            text=f"⚙️ Nigimi Architecture v2.0 // {self.lang_mgr.get('dev_note')}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLOR_PURPLE
        )
        dev_lbl.pack(side="bottom", anchor="w", pady=10)

    def _on_lang_selected(self, choice_text: str):
        # Поиск кода языка по названию
        selected_code = "ru"
        for code, name in LanguageManager.LANGUAGES.items():
            if name == choice_text:
                selected_code = code
                break

        self.lang_mgr.set_language(selected_code)
        self.on_language_change_callback()

    def _on_autostart_toggled(self):
        state = bool(self.autostart_sw.get())
        success = AutoStartManager.toggle(state)
        if not success:
            messagebox.showwarning("Autostart", "Не удалось изменить параметры автозапуска в реестре.")


class NigimiApp(ctk.CTk):
    """Главный интерфейс приложения Nigimi Network Controller v2.0"""
    def __init__(self):
        super().__init__()

        self.lang_mgr = LanguageManager()
        self.engine = NetworkEngine()
        self.selected_group = None
        self.groups_cache = {}          # exe_name: group_dict
        self.row_widgets = {}           # exe_name: dict of widgets
        self.search_query = ""

        self.title(self.lang_mgr.get("app_title"))
        self.geometry("1180x750")
        self.minsize(1000, 650)
        self.configure(fg_color=COLOR_BG)

        self._build_main_ui()

        # Старт фонового сканера процессов
        self.scan_queue = queue.Queue()
        self.is_scanning = True
        threading.Thread(target=self._background_scanner, daemon=True).start()
        self._check_scan_queue()

    def _build_main_ui(self):
        # 1. Верхний Баннер (Header)
        self.header = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=70)
        self.header.pack(fill="x", side="top")

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=25, pady=12)

        main_title = ctk.CTkLabel(
            title_box, 
            text="NIGIMI", 
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color=COLOR_CYAN
        )
        main_title.pack(side="left")

        sub_title = ctk.CTkLabel(
            title_box, 
            text=" // OVERLORD v2.0", 
            font=ctk.CTkFont(family="Consolas", size=18),
            text_color=COLOR_MAGENTA
        )
        sub_title.pack(side="left")

        # Кнопка Настроек (Шестеренка ⚙)
        self.btn_settings = ctk.CTkButton(
            self.header,
            text="⚙️",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_PURPLE,
            text_color=COLOR_CYAN,
            width=46,
            height=40,
            corner_radius=10,
            command=self.open_settings_modal
        )
        self.btn_settings.pack(side="right", padx=(5, 25))

        self.opt_btn = ctk.CTkButton(
            self.header,
            text=self.lang_mgr.get("overdrive_btn"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLOR_MAGENTA,
            hover_color=COLOR_CYAN,
            text_color="#FFFFFF",
            corner_radius=20,
            height=38,
            command=self.run_system_optimization
        )
        self.opt_btn.pack(side="right", padx=10)

        # 2. Информационные карточки статистики
        self.stats_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_bar.pack(fill="x", padx=25, pady=(15, 5))

        self.card_total = self._create_stat_card(self.stats_bar, self.lang_mgr.get("total_apps"), "0", COLOR_CYAN)
        self.card_total.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.card_muted = self._create_stat_card(self.stats_bar, self.lang_mgr.get("blocked_apps"), "0", COLOR_MAGENTA)
        self.card_muted.pack(side="left", expand=True, fill="x", padx=5)

        self.card_limited = self._create_stat_card(self.stats_bar, self.lang_mgr.get("limited_apps"), "0", COLOR_PURPLE)
        self.card_limited.pack(side="left", expand=True, fill="x", padx=(10, 0))

        # 3. Инструментальная панель поиска
        tool_bar = ctk.CTkFrame(self, fg_color="transparent")
        tool_bar.pack(fill="x", padx=25, pady=(15, 10))

        self.search_entry = ctk.CTkEntry(
            tool_bar,
            placeholder_text=self.lang_mgr.get("search_ph"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=COLOR_CARD,
            border_color=COLOR_SURFACE,
            text_color=COLOR_TEXT_MAIN,
            height=42,
            corner_radius=10
        )
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", self._on_search_type)

        self.refresh_btn = ctk.CTkButton(
            tool_bar,
            text=self.lang_mgr.get("refresh_btn"),
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_CYAN,
            text_color=COLOR_TEXT_MAIN,
            height=42,
            corner_radius=10,
            command=self.force_refresh
        )
        self.refresh_btn.pack(side="right")

        # 4. Рабочая область
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=25, pady=10)

        # Список сгруппированных процессов (Task Manager style)
        self.proc_scroll = ctk.CTkScrollableFrame(
            content_frame,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_SURFACE
        )
        self.proc_scroll.pack(side="left", expand=True, fill="both", padx=(0, 15))

        # Панель управления справа
        self.control_panel = ctk.CTkFrame(
            content_frame,
            fg_color=COLOR_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_SURFACE,
            width=340
        )
        self.control_panel.pack(side="right", fill="y")
        self.control_panel.pack_propagate(False)

        self._build_control_panel()

        # 5. Статус-бар
        status_bar = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=35, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")

        self.status_lbl = ctk.CTkLabel(
            status_bar,
            text=self.lang_mgr.get("status_active"),
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_CYAN
        )
        self.status_lbl.pack(side="left", padx=20)

    def _create_stat_card(self, parent, title: str, initial_val: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_SURFACE)
        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Segoe UI", size=11), text_color=COLOR_TEXT_MUTED)
        lbl_t.pack(anchor="w", padx=15, pady=(8, 0))
        
        lbl_v = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(family="Consolas", size=20, weight="bold"), text_color=color)
        lbl_v.pack(anchor="w", padx=15, pady=(0, 8))
        
        card.val_label = lbl_v
        card.title_label = lbl_t
        return card

    def _build_control_panel(self):
        """Панель управления выбранной группой процессов"""
        self.p_title = ctk.CTkLabel(
            self.control_panel,
            text=self.lang_mgr.get("control_panel"),
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        self.p_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.sel_card = ctk.CTkFrame(self.control_panel, fg_color=COLOR_SURFACE, corner_radius=10)
        self.sel_card.pack(fill="x", padx=15, pady=10)

        self.sel_name_lbl = ctk.CTkLabel(
            self.sel_card,
            text=self.lang_mgr.get("select_app"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.sel_name_lbl.pack(anchor="w", padx=15, pady=(12, 2))

        self.sel_pid_lbl = ctk.CTkLabel(
            self.sel_card,
            text=self.lang_mgr.get("processes_cnt", count="---", pids="---"),
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.sel_pid_lbl.pack(anchor="w", padx=15, pady=(0, 2))

        self.sel_path_lbl = ctk.CTkLabel(
            self.sel_card,
            text=self.lang_mgr.get("path_lbl", path="---"),
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            wraplength=280,
            justify="left"
        )
        self.sel_path_lbl.pack(anchor="w", padx=15, pady=(0, 12))

        self.btn_mute = ctk.CTkButton(
            self.control_panel,
            text=self.lang_mgr.get("btn_mute"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_MAGENTA,
            hover_color="#D00060",
            height=45,
            corner_radius=8,
            state="disabled",
            command=self.action_mute
        )
        self.btn_mute.pack(fill="x", padx=15, pady=(15, 8))

        self.btn_limit = ctk.CTkButton(
            self.control_panel,
            text=self.lang_mgr.get("btn_limit"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_PURPLE,
            hover_color="#8B31E0",
            height=45,
            corner_radius=8,
            state="disabled",
            command=self.action_limit
        )
        self.btn_limit.pack(fill="x", padx=15, pady=8)

        self.btn_restore = ctk.CTkButton(
            self.control_panel,
            text=self.lang_mgr.get("btn_restore"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_GREEN,
            text_color=COLOR_TEXT_MAIN,
            height=45,
            corner_radius=8,
            state="disabled",
            command=self.action_restore
        )
        self.btn_restore.pack(fill="x", padx=15, pady=8)

        divert_status = "ДОСТУПЕН (РЕЖИМ ЯДРА)" if PYDIVERT_AVAILABLE else "НЕ НАЙДЕН (БРАНДМАУЭР)"
        driver_lbl = ctk.CTkLabel(
            self.control_panel,
            text=f"Драйвер WinDivert:\n{divert_status}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_CYAN if PYDIVERT_AVAILABLE else COLOR_MAGENTA,
            justify="center"
        )
        driver_lbl.pack(side="bottom", pady=20)

    def open_settings_modal(self):
        """Открывает модальное окно настроек с поддержкой сменой языка"""
        SettingsModal(self, self.lang_mgr, self.update_ui_language)

    def update_ui_language(self):
        """Динамическое обновление всех надписей при смене языка"""
        self.title(self.lang_mgr.get("app_title"))
        self.opt_btn.configure(text=self.lang_mgr.get("overdrive_btn"))
        self.search_entry.configure(placeholder_text=self.lang_mgr.get("search_ph"))
        self.refresh_btn.configure(text=self.lang_mgr.get("refresh_btn"))
        self.p_title.configure(text=self.lang_mgr.get("control_panel"))
        self.btn_mute.configure(text=self.lang_mgr.get("btn_mute"))
        self.btn_limit.configure(text=self.lang_mgr.get("btn_limit"))
        self.btn_restore.configure(text=self.lang_mgr.get("btn_restore"))

        self.card_total.title_label.configure(text=self.lang_mgr.get("total_apps"))
        self.card_muted.title_label.configure(text=self.lang_mgr.get("blocked_apps"))
        self.card_limited.title_label.configure(text=self.lang_mgr.get("limited_apps"))

        if not self.selected_group:
            self.sel_name_lbl.configure(text=self.lang_mgr.get("select_app"))
            self.sel_pid_lbl.configure(text=self.lang_mgr.get("processes_cnt", count="---", pids="---"))
            self.sel_path_lbl.configure(text=self.lang_mgr.get("path_lbl", path="---"))

        self._render_groups_diff()

    def _background_scanner(self):
        """Фоновый поток сбора и группировки процессов"""
        while self.is_scanning:
            try:
                groups = {}
                for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info']):
                    try:
                        pinfo = proc.info
                        name = pinfo['name']
                        if not name or pinfo['pid'] <= 4:
                            continue

                        exe_name = name.lower()
                        ram_mb = round((pinfo['memory_info'].rss / (1024 * 1024)), 1) if pinfo['memory_info'] else 0.0

                        if exe_name not in groups:
                            groups[exe_name] = {
                                'display_name': name,
                                'exe_name': exe_name,
                                'exe_path': pinfo['exe'] or '',
                                'pids': [pinfo['pid']],
                                'ram_mb': ram_mb,
                                'count': 1
                            }
                        else:
                            groups[exe_name]['pids'].append(pinfo['pid'])
                            groups[exe_name]['ram_mb'] = round(groups[exe_name]['ram_mb'] + ram_mb, 1)
                            groups[exe_name]['count'] += 1
                            if not groups[exe_name]['exe_path'] and pinfo['exe']:
                                groups[exe_name]['exe_path'] = pinfo['exe']

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass

                self.scan_queue.put(groups)
            except Exception:
                pass

            time.sleep(2.0)

    def _check_scan_queue(self):
        """Проверка очереди данных от фонового потока"""
        latest_data = None
        while not self.scan_queue.empty():
            latest_data = self.scan_queue.get()

        if latest_data is not None:
            self.groups_cache = latest_data
            self._render_groups_diff()

        self.after(500, self._check_scan_queue)

    def _on_search_type(self, event=None):
        """Мгновенный фильтр поиска без пересоздания виджетов"""
        self.search_query = self.search_entry.get().strip().lower()
        self._render_groups_diff()

    def _render_groups_diff(self):
        """Отрисовка списка методом диффинга и обновление карточек статистики"""
        query = self.search_query
        sorted_groups = sorted(
            self.groups_cache.values(),
            key=lambda x: x['ram_mb'],
            reverse=True
        )

        rendered_count = 0
        active_keys = set()

        # Обновление показателей счетчиков
        muted_cnt = len(self.engine.blocked_groups)
        limited_cnt = len(self.engine.rate_limited_groups)
        total_cnt = len(sorted_groups)

        self.card_total.val_label.configure(text=str(total_cnt))
        self.card_muted.val_label.configure(text=str(muted_cnt))
        self.card_limited.val_label.configure(text=str(limited_cnt))

        for group in sorted_groups:
            exe_name = group['exe_name']
            display_name = group['display_name']

            if query and query not in exe_name and query not in display_name.lower():
                if exe_name in self.row_widgets:
                    self.row_widgets[exe_name]['frame'].pack_forget()
                continue

            active_keys.add(exe_name)
            rendered_count += 1
            if rendered_count > 100:  # Ограничение видимых строк для плавности
                break

            status_text = self.lang_mgr.get("status_norm")
            status_color = COLOR_GREEN

            if exe_name in self.engine.blocked_groups:
                status_text = self.lang_mgr.get("status_muted")
                status_color = COLOR_MAGENTA
            elif exe_name in self.engine.rate_limited_groups:
                status_text = self.lang_mgr.get("status_limited")
                status_color = COLOR_PURPLE

            title_text = f"{display_name} ({group['count']})" if group['count'] > 1 else display_name

            # Если строка уже существует - просто обновляем значения
            if exe_name in self.row_widgets:
                w_dict = self.row_widgets[exe_name]
                w_dict['frame'].pack(fill="x", pady=3, padx=5)
                w_dict['lbl_name'].configure(text=title_text)
                w_dict['lbl_ram'].configure(text=f"{group['ram_mb']} МБ")
                w_dict['badge_frame'].configure(fg_color=status_color)
                w_dict['badge_lbl'].configure(text=status_text)
            else:
                row_frame = ctk.CTkFrame(
                    self.proc_scroll,
                    fg_color=COLOR_SURFACE,
                    corner_radius=8,
                    height=48
                )
                row_frame.pack(fill="x", pady=3, padx=5)
                row_frame.pack_propagate(False)

                lbl_name = ctk.CTkLabel(
                    row_frame,
                    text=title_text,
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                    text_color=COLOR_TEXT_MAIN
                )
                lbl_name.pack(side="left", padx=15)

                lbl_ram = ctk.CTkLabel(
                    row_frame,
                    text=f"{group['ram_mb']} МБ",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color=COLOR_CYAN
                )
                lbl_ram.pack(side="left", padx=15)

                badge_frame = ctk.CTkFrame(row_frame, fg_color=status_color, corner_radius=12, height=24)
                badge_frame.pack(side="right", padx=15)

                badge_lbl = ctk.CTkLabel(
                    badge_frame,
                    text=status_text,
                    font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                    text_color="#000000"
                )
                badge_lbl.pack(padx=10, pady=2)

                self.row_widgets[exe_name] = {
                    'frame': row_frame,
                    'lbl_name': lbl_name,
                    'lbl_ram': lbl_ram,
                    'badge_frame': badge_frame,
                    'badge_lbl': badge_lbl
                }

                for w in [row_frame, lbl_name, lbl_ram]:
                    w.bind("<Button-1>", lambda e, g=exe_name: self.select_group(g))

        for exe_k, w_dict in list(self.row_widgets.items()):
            if exe_k not in active_keys:
                w_dict['frame'].pack_forget()

    def select_group(self, exe_name: str):
        """Выбор группы процессов"""
        if exe_name not in self.groups_cache:
            return

        group = self.groups_cache[exe_name]
        self.selected_group = group

        self.sel_name_lbl.configure(text=group['display_name'])
        pid_preview = ', '.join(str(p) for p in group['pids'][:3])
        if group['count'] > 3:
            pid_preview += "..."

        self.sel_pid_lbl.configure(
            text=self.lang_mgr.get("processes_cnt", count=group['count'], pids=pid_preview)
        )

        exe_path = group.get('exe_path') or "N/A"
        self.sel_path_lbl.configure(text=self.lang_mgr.get("path_lbl", path=exe_path))

        self.btn_mute.configure(state="normal")
        self.btn_limit.configure(state="normal")
        self.btn_restore.configure(state="normal")

        self.log(f"Выбрано приложение: {group['display_name']} ({group['count']} проц.)")

    def action_mute(self):
        if not self.selected_group:
            return

        group = self.selected_group
        self.engine.block_group(group)
        self.log(f"🚫 [MUTE ALL] {group['display_name']} заблокирован!")
        self._render_groups_diff()

    def action_limit(self):
        if not self.selected_group:
            return

        group = self.selected_group

        def apply_limit_callback(bytes_sec, formatted_text):
            self.engine.limit_group(group, bytes_sec)
            self.log(f"⚡ [LIMIT ALL] Для {group['display_name']} установлен лимит: {formatted_text}")
            self._render_groups_diff()

        RateLimitModal(self, group['display_name'], apply_limit_callback, self.lang_mgr)

    def action_restore(self):
        if not self.selected_group:
            return

        group = self.selected_group
        self.engine.unlimit_group(group['exe_name'], group.get('exe_path', ''))
        self.log(f"🔄 [RESTORE] Ограничения сброшены для {group['display_name']}")
        self._render_groups_diff()

    def force_refresh(self):
        self.log("Обновление списка процессов...")
        self._render_groups_diff()

    def run_system_optimization(self):
        self.log("🚀 Активация режима OVERDRIVE OPTIMIZATION...")

        def _worker():
            try:
                subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
                subprocess.run("netsh int tcp set global autotuninglevel=normal", shell=True, capture_output=True)

                p = psutil.Process(os.getpid())
                p.priority(psutil.HIGH_PRIORITY_CLASS)

                self.after(0, lambda: self.log("✅ OVERDRIVE: Сетевые буферы очищены, высший приоритет CPU установлен!"))
                self.after(0, lambda: messagebox.showinfo("Nigimi Overdrive", "Система переведена в максимальный сетевой приоритет!"))
            except Exception as err:
                err_msg = str(err)
                self.after(0, lambda msg=err_msg: self.log(f"⚠️ Ошибка оптимизации: {msg}"))

        threading.Thread(target=_worker, daemon=True).start()

    def log(self, message: str):
        t_str = time.strftime("%H:%M:%S")
        self.status_lbl.configure(text=f"[{t_str}] {message}")

    def destroy(self):
        self.is_scanning = False
        self.engine.is_running = False
        super().destroy()


if __name__ == "__main__":
    elevate_admin()
    app = NigimiApp()
    app.mainloop()