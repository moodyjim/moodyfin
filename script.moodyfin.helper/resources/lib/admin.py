"""MoodyFin admin pages (window 1154): Jellyfin's admin pages for a remote, in the Jellyfin theme's admin look.

The page is Window(Home).Property(MoodyFin.AdminPage): general, users, libraries, devices, activity, plugins, tasks.
While window 1154 is open the service calls Admin.tick(); it reads the page from the server when the page changes,
after an action (MoodyFin.Admin.Dirty), and every few seconds (running tasks / scans faster). Rows land as JSON in
Window(Home).Property(MoodyFin.Admin.Rows) ({page, rows}; + .Reload, .Count, .Title) for plugin://...?row=admin.

Every row has: id, title, sub, right, chip, chipc (accent|green|red|orange|muted), icon (a moodyfin/icons name),
pic (a picture URL), round ("1" = circle picture), pct (progress, "" = none).

Selecting a row: RunScript(script.moodyfin.helper,action=admin,id=...) -> act(): Kodi's own pickers, and a yes / no
before anything that can't be undone. Toolbar: action=admintool (Libraries: scan all; Activity: which entries).
"""
import datetime
import hashlib
import json
import threading
import time
from urllib.parse import quote, urlencode

import xbmc
import xbmcgui

from . import jellyfin

HOME = xbmcgui.Window(10000)
P = "MoodyFin.Admin."
WINDOW = "Window.IsActive(1154)"
EVERY = {"general": 60, "users": 30, "libraries": 10, "devices": 30, "activity": 15, "plugins": 60, "tasks": 10}
TITLES = {"general": "General", "users": "Users", "libraries": "Libraries", "devices": "Devices",
          "activity": "Activity", "plugins": "Plugins", "tasks": "Scheduled tasks"}
LIB_ICON = {"movies": "movie", "tvshows": "tv", "music": "music_note", "boxsets": "video_library"}
LIB_TYPE = {"movies": "Movies", "tvshows": "Shows", "music": "Music", "boxsets": "Collections", "books": "Books",
            "homevideos": "Home videos", "musicvideos": "Music videos", "mixed": "Mixed", None: "Mixed"}
PLUGIN_CHIP = {"Active": ("Active", "green"), "Restart": ("Restart needed", "orange"), "Disabled": ("Disabled", "muted"),
               "Malfunctioned": ("Malfunctioned", "red"), "NotSupported": ("Not supported", "red"),
               "Superceded": ("Superseded", "muted"), "Superseded": ("Superseded", "muted"), "Deleted": ("Removed", "muted")}
# General: (config key, label, what it is, kind)
GENERAL = [
    ("ServerName", "Server name", "Shown to clients and on the dashboard", "text"),
    ("UICulture", "Display language", "The server's own language (dashboard, notifications)", "culture"),
    ("PreferredMetadataLanguage", "Metadata language", "Preferred language for downloaded metadata", "language"),
    ("MetadataCountryCode", "Country", "For ratings and release dates", "country"),
    ("QuickConnectAvailable", "Quick Connect", "Sign in on a new device with a code", "bool"),
    ("LibraryScanFanoutConcurrency", "Parallel library scan tasks", "0 = automatic", "int"),
    ("ParallelImageEncodingLimit", "Parallel image encoding", "0 = automatic", "int"),
    ("ActivityLogRetentionDays", "Activity log kept for", "Days (empty = forever)", "int"),
    ("CachePath", "Cache path", "Read only here (change it in the web dashboard)", "path"),
    ("MetadataPath", "Metadata path", "Read only here (change it in the web dashboard)", "path"),
]


def _parse(iso):
    try:
        return datetime.datetime.fromisoformat(str(iso)[:19]).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def _ago(iso):
    d = _parse(iso)
    if not d:
        return ""
    s = (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds()
    if s < 90:
        return "just now"
    if s < 3600:
        return "%d min ago" % (s // 60)
    if s < 86400:
        return "%d h ago" % (s // 3600)
    if s < 86400 * 60:
        return "%d days ago" % (s // 86400)
    return d.astimezone().strftime("%b %d, %Y")


def _took(r):
    a, b = _parse(r.get("StartTimeUtc")), _parse(r.get("EndTimeUtc"))
    if not a or not b:
        return ""
    s = int((b - a).total_seconds())
    return "%ds" % s if s < 60 else "%dm %ds" % (s // 60, s % 60) if s < 3600 else "%dh %dm" % (s // 3600, s % 3600 // 60)


def _when(iso):
    d = _parse(iso)
    if not d:
        return ""
    d = d.astimezone()
    return d.strftime("%I:%M %p") if d.date() == datetime.date.today() else d.strftime("%a %b %d · %I:%M %p")


def _words(t):
    """VideoPlaybackStopped -> Video playback stopped"""
    import re
    w = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", t or "").split(" ")
    return " ".join([w[0]] + [x.lower() for x in w[1:]]) if w and w[0] else ""


def _row(**kw):
    out = {k: "" for k in ("id", "title", "sub", "right", "chip", "chipc", "icon", "pic", "round", "pct")}
    out.update({k: ("" if v is None else str(v)) for k, v in kw.items()})
    return out


def _q(path, **params):
    return path + "?" + urlencode({k: v for k, v in params.items() if v is not None})


# ---------------------------------------------------------------- reading the pages
class Admin:
    def __init__(self):
        self.page = None
        self.due = 0
        self.busy = False

    def tick(self):
        if not xbmc.getCondVisibility(WINDOW):
            self.page = None
            return
        page = HOME.getProperty("MoodyFin.AdminPage") or "users"
        now = time.time()
        if page != self.page:
            self.page, self.due = page, 0
            HOME.setProperty(P + "Title", TITLES.get(page, ""))
            HOME.setProperty(P + "Rows", json.dumps({"page": page, "rows": []}))
            HOME.setProperty(P + "Reload", "%s-0" % page)
            HOME.setProperty(P + "Count", "")
        if HOME.getProperty(P + "Dirty"):
            HOME.clearProperty(P + "Dirty")
            self.due = 0
        if self.busy or now < self.due:
            return
        fast = HOME.getProperty(P + "Busy") == "1"
        self.due = now + (3 if fast else EVERY.get(page, 30))
        self.busy = True
        threading.Thread(target=self._load, args=(page,), daemon=True).start()

    def _load(self, page):
        try:
            rows = getattr(self, "_" + page)()
            if page != self.page:
                return
            raw = json.dumps({"page": page, "rows": rows}, separators=(",", ":"))
            if HOME.getProperty(P + "Rows") != raw:
                HOME.setProperty(P + "Rows", raw)
                HOME.setProperty(P + "Reload", "%s-%s" % (page, hashlib.md5(raw.encode()).hexdigest()[:10]))
            HOME.setProperty(P + "Count", str(len(rows)) if page not in ("general",) else "")
        except jellyfin.JellyfinError as e:
            HOME.setProperty(P + "Error", str(e))
        except Exception as exc:
            xbmc.log("[moodyfin] admin %s: %r" % (page, exc), xbmc.LOGWARNING)
        finally:
            self.busy = False

    @staticmethod
    def _address():
        return jellyfin._login()[0]

    def _users(self):
        address, me = self._address(), jellyfin.me()
        users = jellyfin.call("GET", "/Users") or []
        users.sort(key=lambda u: (u.get("Name") or "").lower())
        rows = []
        for u in users:
            pol = u.get("Policy") or {}
            sub = ["Administrator" if pol.get("IsAdministrator") else "User"]
            if not u.get("HasPassword"):
                sub.append("no password")
            if not pol.get("EnableRemoteAccess", True):
                sub.append("home network only")
            if u.get("Id") == me:
                sub.append("you")
            chip, chipc = ("Disabled", "red") if pol.get("IsDisabled") else ("Admin", "accent") if pol.get("IsAdministrator") else ("", "")
            tag = u.get("PrimaryImageTag")
            pic = _q("%s/Users/%s/Images/Primary" % (address, u["Id"]), tag=tag, maxWidth=96, quality=90) if tag else ""
            rows.append(_row(id=u["Id"], title=u.get("Name"), sub=" · ".join(sub), chip=chip, chipc=chipc,
                             right=("Active " + _ago(u.get("LastActivityDate"))) if u.get("LastActivityDate") else "Never signed in",
                             icon="person", pic=pic, round="1"))
        return rows

    def _libraries(self):
        libs = jellyfin.call("GET", "/Library/VirtualFolders") or []
        rows, busy = [], False
        for lib in libs:
            ct = lib.get("CollectionType")
            loc = lib.get("Locations") or []
            status = lib.get("RefreshStatus") or "Idle"
            pct = lib.get("RefreshProgress")
            scanning = status != "Idle"
            busy = busy or scanning
            rows.append(_row(id=lib.get("ItemId"), title=lib.get("Name"),
                             sub="%s · %s" % (LIB_TYPE.get(ct, (ct or "Mixed").title()), ", ".join(loc) or "no folders"),
                             right="%d folder%s" % (len(loc), "" if len(loc) == 1 else "s"),
                             chip=("Scanning %d%%" % pct) if scanning and pct is not None else ("Scanning" if scanning else ""),
                             chipc="accent", icon=LIB_ICON.get(ct, "video_library"),
                             pct=int(pct) if scanning and pct is not None else ""))
        HOME.setProperty(P + "Busy", "1" if busy else "")
        return rows

    def _tasks(self):
        tasks = jellyfin.call("GET", _q("/ScheduledTasks", isHidden="false")) or []
        tasks.sort(key=lambda t: ((t.get("Category") or "").lower(), (t.get("Name") or "").lower()))
        rows, busy = [], False
        for t in tasks:
            r = t.get("LastExecutionResult") or {}
            state = t.get("State") or "Idle"
            running = state == "Running"
            busy = busy or running
            pct = t.get("CurrentProgressPercentage")
            last = ("last run " + _ago(r.get("EndTimeUtc")) + (", took " + _took(r) if _took(r) else "")) if r.get("EndTimeUtc") else "never run"
            chip, chipc = "", ""
            if running:
                chip, chipc = ("Running %d%%" % pct) if pct is not None else "Running", "accent"
            elif state == "Cancelling":
                chip, chipc = "Stopping", "orange"
            elif r.get("Status") == "Failed":
                chip, chipc = "Failed", "red"
            elif r.get("Status") == "Cancelled":
                chip, chipc = "Stopped", "orange"
            rows.append(_row(id=t.get("Id"), title=t.get("Name"), sub="%s · %s" % (t.get("Category") or "", last),
                             right=(t.get("Description") or "")[:60], chip=chip, chipc=chipc, icon="schedule",
                             pct=int(pct) if running and pct is not None else ""))
        HOME.setProperty(P + "Busy", "1" if busy else "")
        return rows

    def _devices(self):
        r = jellyfin.call("GET", "/Devices") or {}
        devices = r.get("Items") if isinstance(r, dict) else r
        devices = sorted(devices or [], key=lambda d: d.get("DateLastActivity") or "", reverse=True)
        mine = jellyfin.device_id()
        rows = []
        for d in devices:
            this = d.get("Id") == mine
            rows.append(_row(id=d.get("Id"), title=d.get("CustomName") or d.get("Name"),
                             sub=" ".join(x for x in (d.get("AppName"), d.get("AppVersion")) if x),
                             right="%s · %s" % (d.get("LastUserName") or "—", _ago(d.get("DateLastActivity"))),
                             chip="This device" if this else "", chipc="accent", icon="devices"))
        return rows

    def _activity(self):
        flt = HOME.getProperty(P + "Filter") or "all"
        params = {"startIndex": 0, "limit": 100}
        if flt != "all":
            params["hasUserId"] = "true" if flt == "user" else "false"
        log = (jellyfin.call("GET", _q("/System/ActivityLog/Entries", **params)) or {}).get("Items") or []
        address = self._address()
        users = {u["Id"]: u for u in jellyfin.call("GET", "/Users") or []}
        rows = []
        for e in log:
            sev = e.get("Severity") or ""
            u = users.get(e.get("UserId") or "")
            tag = u.get("PrimaryImageTag") if u else None
            t = e.get("Type") or ""
            icon = ("play_arrow" if "Playback" in t else "person" if ("Session" in t or "Authentication" in t) else
                    "extension" if ("Plugin" in t or "Install" in t or "Update" in t) else "history")
            rows.append(_row(id=e.get("Id"), title=e.get("Name"), sub=e.get("ShortOverview") or _words(t),
                             right=_when(e.get("Date")), chip=("Error" if sev == "Error" else "Warning" if sev == "Warning" else ""),
                             chipc="red" if sev == "Error" else "orange", icon=icon,
                             pic=_q("%s/Users/%s/Images/Primary" % (address, u["Id"]), tag=tag, maxWidth=96, quality=90) if tag else "",
                             round="1"))
        self.log = {str(e.get("Id")): e for e in log}
        return rows

    def _plugins(self):
        plugins = sorted(jellyfin.call("GET", "/Plugins") or [], key=lambda x: (x.get("Name") or "").lower())
        rows = []
        for p in plugins:
            chip, chipc = PLUGIN_CHIP.get(p.get("Status") or "", (p.get("Status") or "", "muted"))
            desc = (p.get("Description") or "").strip().split("\n")[0]
            rows.append(_row(id="%s|%s" % (p.get("Id"), p.get("Version")), title=p.get("Name"),
                             sub=(desc[:110] + "…") if len(desc) > 110 else desc, right="v" + str(p.get("Version") or ""),
                             chip=chip, chipc=chipc, icon="extension"))
        return rows

    def _general(self):
        c = jellyfin.call("GET", "/System/Configuration") or {}
        names = {}
        try:
            names["UICulture"] = {o.get("Value"): o.get("Name") for o in jellyfin.call("GET", "/Localization/Options") or []}
            names["PreferredMetadataLanguage"] = {o.get("TwoLetterISOLanguageName"): o.get("DisplayName")
                                                  for o in jellyfin.call("GET", "/Localization/Cultures") or []}
            names["MetadataCountryCode"] = {o.get("TwoLetterISORegionName"): o.get("DisplayName")
                                            for o in jellyfin.call("GET", "/Localization/Countries") or []}
        except jellyfin.JellyfinError:
            pass
        rows = []
        for key, label, what, kind in GENERAL:
            v = c.get(key)
            if kind == "bool":
                shown = "On" if v else "Off"
            elif kind == "path":
                shown = v or "default"
            elif kind == "int":
                shown = "automatic" if v in (0, None) and key != "ActivityLogRetentionDays" else ("forever" if v in (None, 0) else str(v))
            else:
                shown = names.get(key, {}).get(v, v) or "—"
            rows.append(_row(id=key, title=label, sub=what, right=shown, icon="settings",
                             chip="Read only" if kind == "path" else "", chipc="muted"))
        return rows


# ---------------------------------------------------------------- plugin rows
def _rows():
    try:
        return json.loads(HOME.getProperty(P + "Rows") or "{}")
    except ValueError:
        return {}


def rows(reload=""):
    """The rows, only when they belong to the page the list asked for (its reload is "<page>-<hash>")."""
    got = _rows()
    data = got.get("rows") or []
    if reload and not reload.startswith((got.get("page") or "?") + "-"):
        data = []
    out = []
    for d in data:
        li = xbmcgui.ListItem(d.get("title", ""), offscreen=True)
        for k, v in d.items():
            li.setProperty("mf." + k, v)
        li.setArt({"thumb": d.get("pic", ""), "icon": "moodyfin/icons/%s.png" % (d.get("icon") or "settings")})
        out.append((li, False))
    return out


# ---------------------------------------------------------------- actions
def _done(msg=None):
    HOME.setProperty(P + "Dirty", "1")
    if msg:
        xbmcgui.Dialog().notification("MoodyFin", msg, xbmcgui.NOTIFICATION_INFO, 2500)


def _err(e):
    xbmcgui.Dialog().notification("MoodyFin", str(e), xbmcgui.NOTIFICATION_WARNING, 4000)


def _row_title(rid):
    for d in _rows().get("rows") or []:
        if d.get("id") == rid:
            return d.get("title", "")
    return ""


def act(rid):
    page = HOME.getProperty("MoodyFin.AdminPage")
    try:
        {"users": _act_user, "libraries": _act_library, "tasks": _act_task, "devices": _act_device,
         "activity": _act_activity, "plugins": _act_plugin, "general": _act_general}.get(page, lambda r: None)(rid)
    except jellyfin.JellyfinError as e:
        _err(e)


def tool():
    page = HOME.getProperty("MoodyFin.AdminPage")
    try:
        if page == "libraries":
            jellyfin.call("POST", "/Library/Refresh")
            HOME.setProperty(P + "Busy", "1")
            _done("Scanning all libraries")
        elif page == "activity":
            order = ["all", "user", "system"]
            cur = HOME.getProperty(P + "Filter") or "all"
            HOME.setProperty(P + "Filter", order[(order.index(cur) + 1) % 3] if cur in order else "all")
            _done()
    except jellyfin.JellyfinError as e:
        _err(e)


def _act_user(uid):
    u = jellyfin.call("GET", "/Users/%s" % uid) or {}
    pol = u.get("Policy") or {}
    name = u.get("Name") or ""
    me = uid == jellyfin.me()
    opts = []
    if not me:
        opts.append(("enable", "Enable user") if pol.get("IsDisabled") else ("disable", "Disable user"))
        opts.append(("noadmin", "Remove administrator") if pol.get("IsAdministrator") else ("admin", "Make administrator"))
    opts.append(("remote", "Allow access from outside the home" if not pol.get("EnableRemoteAccess", True)
                 else "Home network only"))
    opts.append(("reset", "Reset password"))
    if not me:
        opts.append(("delete", "Delete user"))
    pick = xbmcgui.Dialog().select(name, [o[1] for o in opts])
    if pick < 0:
        return
    what = opts[pick][0]
    if what == "delete":
        if xbmcgui.Dialog().yesno("Delete %s" % name, "Their account, settings and watch history go. This can't be undone.",
                                  nolabel="Cancel", yeslabel="Delete"):
            jellyfin.call("DELETE", "/Users/%s" % uid)
            _done("%s deleted" % name)
        return
    if what == "reset":
        if xbmcgui.Dialog().yesno("Reset %s's password" % name, "The password is removed: they sign in without one until they set a new one.",
                                  nolabel="Cancel", yeslabel="Reset"):
            jellyfin.call("POST", "/Users/%s/Password" % uid, {"ResetPassword": True})
            _done("Password reset")
        return
    if what in ("disable", "noadmin") and not xbmcgui.Dialog().yesno(
            opts[pick][1], "%s: %s?" % (name, opts[pick][1].lower()), nolabel="Cancel", yeslabel="Yes"):
        return
    pol = dict(pol)
    if what in ("enable", "disable"):
        pol["IsDisabled"] = what == "disable"
    elif what in ("admin", "noadmin"):
        pol["IsAdministrator"] = what == "admin"
    elif what == "remote":
        pol["EnableRemoteAccess"] = not pol.get("EnableRemoteAccess", True)
    jellyfin.call("POST", "/Users/%s/Policy" % uid, pol)
    _done("Saved")


def _act_library(item_id):
    name = _row_title(item_id)
    pick = xbmcgui.Dialog().select(name, ["Scan this library", "Scan all libraries"])
    if pick == 0:
        jellyfin.call("POST", _q("/Items/%s/Refresh" % item_id, Recursive="true", ImageRefreshMode="Default",
                                 MetadataRefreshMode="Default", ReplaceAllImages="false", ReplaceAllMetadata="false"))
        HOME.setProperty(P + "Busy", "1")
        _done("Scanning %s" % name)
    elif pick == 1:
        jellyfin.call("POST", "/Library/Refresh")
        HOME.setProperty(P + "Busy", "1")
        _done("Scanning all libraries")


def _act_task(tid):
    t = jellyfin.call("GET", "/ScheduledTasks/%s" % tid) or {}
    running = t.get("State") == "Running"
    pick = xbmcgui.Dialog().select(t.get("Name") or "", ["Stop" if running else "Run now"])
    if pick != 0:
        return
    jellyfin.call("DELETE" if running else "POST", "/ScheduledTasks/Running/%s" % tid)
    HOME.setProperty(P + "Busy", "1")
    _done("Stopping" if running else "Started")


def _act_device(did):
    name = _row_title(did)
    mine = did == jellyfin.device_id()
    opts = ["Rename"] + ([] if mine else ["Remove"])
    pick = xbmcgui.Dialog().select(name, opts)
    if pick == 0:
        new = xbmcgui.Dialog().input("Name for this device", name)
        if new and new != name:
            jellyfin.call("POST", _q("/Devices/Options", id=did), {"CustomName": new})
            _done("Renamed")
    elif pick == 1 and xbmcgui.Dialog().yesno("Remove %s" % name, "It's signed out and has to sign in again.",
                                              nolabel="Cancel", yeslabel="Remove"):
        jellyfin.call("DELETE", _q("/Devices", id=did))
        _done("Removed")


def _act_activity(eid):
    log = (jellyfin.call("GET", _q("/System/ActivityLog/Entries", startIndex=0, limit=100)) or {}).get("Items") or []
    e = next((x for x in log if str(x.get("Id")) == str(eid)), None)
    if not e:
        return
    text = "%s\n\n%s\n\n%s" % (_when(e.get("Date")), e.get("Overview") or e.get("ShortOverview") or "", e.get("Type") or "")
    xbmcgui.Dialog().textviewer(e.get("Name") or "", text)


def _act_plugin(rid):
    pid, version = rid.split("|", 1)
    p = next((x for x in jellyfin.call("GET", "/Plugins") or [] if x.get("Id") == pid), {})
    name = p.get("Name") or ""
    opts = [("enable", "Enable") if p.get("Status") == "Disabled" else ("disable", "Disable")]
    if p.get("CanUninstall"):
        opts.append(("uninstall", "Uninstall"))
    pick = xbmcgui.Dialog().select(name, [o[1] for o in opts])
    if pick < 0:
        return
    what = opts[pick][0]
    base = "/Plugins/%s/%s" % (pid, quote(version))
    if what == "uninstall":
        if xbmcgui.Dialog().yesno("Uninstall %s" % name, "It's removed when the server restarts.", nolabel="Cancel", yeslabel="Uninstall"):
            jellyfin.call("DELETE", base)
            _done("Restart the server to finish")
        return
    jellyfin.call("POST", base + ("/Enable" if what == "enable" else "/Disable"))
    _done("Restart the server to finish")


def _act_general(key):
    item = next((g for g in GENERAL if g[0] == key), None)
    if not item:
        return
    _, label, what, kind = item
    if kind == "path":
        xbmcgui.Dialog().ok(label, "Server folders are changed in Jellyfin's web dashboard.")
        return
    c = jellyfin.call("GET", "/System/Configuration") or {}
    v = c.get(key)
    if kind == "text":
        new = xbmcgui.Dialog().input(label, v or "")
        if not new or new == v:
            return
    elif kind == "bool":
        new = not v
    elif kind == "int":
        raw = xbmcgui.Dialog().numeric(0, label, str(v or 0))
        if raw == "" or not raw.isdigit():
            return
        new = int(raw)
    else:
        path, k, n = {"culture": ("/Localization/Options", "Value", "Name"),
                      "language": ("/Localization/Cultures", "TwoLetterISOLanguageName", "DisplayName"),
                      "country": ("/Localization/Countries", "TwoLetterISORegionName", "DisplayName")}[kind]
        opts = sorted(jellyfin.call("GET", path) or [], key=lambda o: (o.get(n) or "").lower())
        pre = next((i for i, o in enumerate(opts) if o.get(k) == v), -1)
        pick = xbmcgui.Dialog().select(label, [o.get(n) or "" for o in opts], preselect=pre)
        if pick < 0:
            return
        new = opts[pick].get(k)
    c[key] = new
    jellyfin.call("POST", "/System/Configuration", c)
    _done("Saved")
