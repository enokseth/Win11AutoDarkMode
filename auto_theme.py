import threading
import ctypes
import datetime
import geocoder
import winreg
import sys
import os
import time
import subprocess
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun
from win11toast import toast
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

# === ÉLÉVATION ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

print("[Élévation] Administrateur :", is_admin())
if not is_admin():
    print("⚠️ Le programme doit être lancé en administrateur pour fonctionner correctement.")
    # Tu peux forcer la relance en admin ici si besoin

# === NOTIFICATION DÉTAILLÉE ===
def show_detailed_notification(mode, location, now, s):
    theme_name = "clair ☀️" if mode == "light" else "sombre 🌙"
    message = (
        f"Thème activé : {theme_name}\n"
        f"Heure actuelle : {now.strftime('%H:%M:%S')}\n"
        f"Lever du soleil : {s['sunrise'].strftime('%H:%M:%S')}\n"
        f"Coucher du soleil : {s['sunset'].strftime('%H:%M:%S')}\n"
        f"Localisation : {location.name}, {location.region}"
    )
    print(f"[Notification détaillée]\n{message}")
    try:
        toast("Auto Theme", message)
    except Exception as e:
        print(f"[Erreur toast] {e}")
        
# === RAFRAÎCHIR LE THÈME (sans tuer explorer) ===
def refresh_theme():
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_ulong()

    # On passe la chaîne "ImmersiveColorSet" pour notifier le changement de thème
    lparam = ctypes.create_unicode_buffer("ImmersiveColorSet")

    res = ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        ctypes.byref(lparam),
        SMTO_ABORTIFHUNG,
        5000,
        ctypes.byref(result)
    )
    print(f"[Thème] Rafraîchissement envoyé, résultat: {res}")

# === NOTIFICATION SIMPLE ===
def show_notification(message):
    print(f"[Notification] {message}")
    try:
        toast("Auto Theme", message)
    except Exception as e:
        print(f"[Erreur toast] {e}")

# === AJOUT / SUPPRESSION DÉMARRAGE ===
def add_to_startup():
    try:
        exe_path = os.path.abspath(sys.argv[0])
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "AutoTheme"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        print("[Startup] AutoTheme ajouté au démarrage.")
    except Exception as e:
        print(f"[Startup] Erreur ajout au démarrage : {e}")

def remove_from_startup():
    try:
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_ALL_ACCESS) as key:
            winreg.DeleteValue(key, "AutoTheme")
        print("[Startup] AutoTheme supprimé du démarrage.")
    except Exception as e:
        print(f"[Startup] Erreur suppression : {e}")

# === REDÉMARRER EXPLORER POUR APPLIQUER LE THÈME ===
def restart_explorer():
    try:
        subprocess.call(["taskkill", "/f", "/im", "explorer.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        subprocess.Popen(["explorer.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[Explorer] Redémarré pour appliquer le thème.")
    except Exception as e:
        print(f"[Erreur explorer.exe] {e}")

# === APPLIQUER LE THÈME ===
def set_theme(mode, location=None, now=None, s=None):
    personalize_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    dwm_path = r"Software\Microsoft\Windows\DWM"
    value_target = 1 if mode == "light" else 0
    has_changed = False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, personalize_path, 0, winreg.KEY_ALL_ACCESS) as key:
            for name in ("AppsUseLightTheme", "SystemUsesLightTheme"):
                current_value, _ = winreg.QueryValueEx(key, name)
                if current_value != value_target:
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value_target)
                    has_changed = True

        # NE PAS INVERSER ColorPrevalence, on met la même valeur que AppsUseLightTheme
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, dwm_path, 0, winreg.KEY_ALL_ACCESS) as key:
            current_value, _ = winreg.QueryValueEx(key, "ColorPrevalence")
            if current_value != value_target:
                winreg.SetValueEx(key, "ColorPrevalence", 0, winreg.REG_DWORD, value_target)
                has_changed = True

    except Exception as e:
        print(f"[Erreur registre] {e}")

    if has_changed:
        print(f"[Thème] Passage au mode {'clair ☀️' if mode == 'light' else 'sombre 🌙'} détecté. Rafraîchissement...")
        ctypes.windll.user32.PostMessageW(0xFFFF, 0x001A, 0, 1)
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF, 0x001A, 0, 1, 0x0002, 2000, ctypes.byref(ctypes.c_ulong())
        )
        refresh_theme()
        time.sleep(1)
        if location and now and s:
            show_detailed_notification(mode, location, now, s)
    else:
        show_notification(f"Déjà en thème {'clair ☀️' if mode == 'light' else 'sombre 🌙'} ✔️")

# === LOCALISATION ===
def get_location():
    g = geocoder.ip('me')
    if g.ok:
        lat, lon = g.latlng
        tf = TimezoneFinder()
        tz = tf.timezone_at(lat=lat, lng=lon)
        city = g.city or "Inconnu"
        country = g.country or "Inconnu"
        print(f"[Localisation] {city}, {country} ({lat}, {lon}) / {tz}")
        return LocationInfo(city, country, tz, lat, lon)
    else:
        raise Exception("Localisation non détectée.")

# === THÈME AUTOMATIQUE ===
def auto_theme():
    try:
        now = datetime.datetime.now(ZoneInfo(location.timezone))
        s = sun(location.observer, date=now.date(), tzinfo=location.timezone)
        if s["sunrise"] <= now <= s["sunset"]:
            set_theme("light", location, now, s)
        else:
            set_theme("dark", location, now, s)
    except Exception as e:
        print(f"[Erreur auto_theme] {e}")

# === ICON TRAY ===
def create_icon():
    img = Image.new('RGB', (64, 64), color=(45, 100, 200))
    d = ImageDraw.Draw(img)
    d.ellipse([20, 20, 44, 44], fill=(255, 255, 255))
    return img

def quit_app(icon, item):
    remove_from_startup()
    icon.stop()
    sys.exit()

def switch_to_dark(icon, item):
    now = datetime.datetime.now(ZoneInfo(location.timezone))
    set_theme("dark", location, now, sun(location.observer, date=now.date(), tzinfo=location.timezone))

def switch_to_light(icon, item):
    now = datetime.datetime.now(ZoneInfo(location.timezone))
    set_theme("light", location, now, sun(location.observer, date=now.date(), tzinfo=location.timezone))

# === DÉMARRAGE ===
add_to_startup()
try:
    location = get_location()
except Exception as e:
    show_notification("Erreur localisation 🌍")
    sys.exit(1)

icon = Icon("AutoTheme", icon=create_icon(), menu=Menu(
    MenuItem("Activer Thème Clair ☀️", switch_to_light),
    MenuItem("Activer Thème Sombre 🌙", switch_to_dark),
    Menu.SEPARATOR,
    MenuItem("Quitter et désinstaller", quit_app)
))

def run_auto_theme():
    while True:
        auto_theme()
        time.sleep(300)  # Vérifie toutes les 5 minutes

threading.Thread(target=run_auto_theme, daemon=True).start()
icon.run()
