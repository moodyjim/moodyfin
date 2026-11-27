"""Drive the local Kodi for testing, over JSON-RPC on 127.0.0.1:9090
(Settings > Services > Control > "Allow remote control from applications on this system").

    python kodi.py restart              quit Kodi, start it, answer No to Jellyfin's "updates pending" question
    python kodi.py focus                current window and control
    python kodi.py keys down,down,right,wait1,select
    python kodi.py info "System.CurrentControlId|ListItem.Label"
    python kodi.py bool "Skin.HasSetting(mf.top10numbers)|Control.IsVisible(402)"
    python kodi.py shot home            screenshot -> $MOODYFIN_SHOTS (default: ./shots)/home.png
    python kodi.py builtin "Skin.ToggleSetting(mf.top10numbers)"   (needs script.devbuiltin)
    python kodi.py enable skin.moodyfin
    python kodi.py log [n]              last MoodyFin/error lines of kodi.log

Kodi 21 sometimes hangs while quitting after playback; restart force-closes it after 30 s (settings are saved first).
Kodi stops drawing while its window is minimized: screenshots fail and visibility doesn't update. Don't ReloadSkin()
through a script: it crashed Kodi 21.3 here. Restart instead.
"""
import glob
import json
import os
import socket
import subprocess
import sys
import time

KODI_EXE = os.environ.get("KODI_EXE", r"C:\Program Files\Kodi\kodi.exe")
SHOTS = os.path.abspath(os.environ.get("MOODYFIN_SHOTS", "shots"))
LOG = os.path.join(os.environ.get("APPDATA", ""), "Kodi", "kodi.log")
KEYS = {"up": "Input.Up", "down": "Input.Down", "left": "Input.Left", "right": "Input.Right", "select": "Input.Select",
        "back": "Input.Back", "info": "Input.Info", "home": "Input.Home", "menu": "Input.ContextMenu"}


def call(method, params=None, timeout=15):
    s = socket.create_connection(("127.0.0.1", 9090), timeout=timeout)
    req = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        req["params"] = params
    s.sendall(json.dumps(req).encode())
    buf = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                return None
            buf += chunk
            try:  # notifications can come first; wait for our id
                for part in buf.decode("utf-8", "replace").replace("}{", "}\n{").split("\n"):
                    obj = json.loads(part)
                    if obj.get("id") == 1:
                        return obj
            except ValueError:
                continue
    finally:
        s.close()


def info(labels):
    return call("XBMC.GetInfoLabels", {"labels": labels}).get("result", {})


def focus():
    return call("GUI.GetProperties", {"properties": ["currentwindow", "currentcontrol"]}).get("result", {})


def keys(seq):
    for k in (x.strip() for x in seq.split(",")):
        if k.startswith("wait"):
            time.sleep(float(k[4:] or 1))
        elif k in KEYS:
            call(KEYS[k])
        elif k:
            call("Input.ExecuteAction", {"action": k})
        time.sleep(0.35)


def shot(name):
    os.makedirs(SHOTS, exist_ok=True)
    call("Settings.SetSettingValue", {"setting": "debug.screenshotpath", "value": SHOTS + os.sep})
    before = set(glob.glob(os.path.join(SHOTS, "screenshot*.png")))
    call("Input.ExecuteAction", {"action": "screenshot"})
    for _ in range(40):
        time.sleep(0.25)
        new = set(glob.glob(os.path.join(SHOTS, "screenshot*.png"))) - before
        if new:
            time.sleep(0.5)
            dst = os.path.join(SHOTS, name + ".png")
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(new.pop(), dst)
            return dst
    return "no screenshot (is Kodi minimized?)"


def running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq kodi.exe"], capture_output=True, text=True).stdout
    return "kodi.exe" in out.lower()


def restart():
    try:
        call("Application.Quit")
    except OSError:
        pass
    for _ in range(60):
        if not running():
            break
        time.sleep(0.5)
    else:
        # Kodi 21 sometimes hangs at "Stopping all" after playback; settings are already saved by then
        subprocess.run(["taskkill", "/F", "/IM", "kodi.exe"], capture_output=True)
        time.sleep(2)
        print("Kodi hung while quitting: closed it")
    subprocess.Popen([KODI_EXE])
    for _ in range(90):
        time.sleep(1)
        try:
            call("JSONRPC.Ping")
            break
        except OSError:
            pass
    for _ in range(40):  # Jellyfin for Kodi may ask about pending updates: leave the library alone
        time.sleep(1)
        if focus().get("currentwindow", {}).get("id") == 10100 and \
                "updates pending" in info(["Control.GetLabel(9)"]).get("Control.GetLabel(9)", ""):
            keys("right,select")
            print("answered No to Jellyfin's updates question")
            break
    return focus()


def main(cmd, args):
    if cmd == "restart":
        print(restart())
    elif cmd == "focus":
        print(focus())
    elif cmd == "keys":
        keys(args[0])
    elif cmd == "info":
        print(json.dumps(info(args[0].split("|")), indent=1))
    elif cmd == "bool":
        print(json.dumps(call("XBMC.GetInfoBooleans", {"booleans": args[0].split("|")}).get("result"), indent=1))
    elif cmd == "shot":
        print(shot(args[0] if args else "shot"))
    elif cmd == "builtin":
        print(call("Addons.ExecuteAddon", {"addonid": "script.devbuiltin", "params": args}))
    elif cmd == "enable":
        print(call("Addons.SetAddonEnabled", {"addonid": args[0], "enabled": True}))
    elif cmd == "log":
        n = int(args[0]) if args else 40
        with open(LOG, encoding="utf-8", errors="replace") as f:
            hits = [l.rstrip() for l in f if "moodyfin" in l.lower() or " error " in l.lower()]
        print("\n".join(hits[-n:]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "help", sys.argv[2:])
