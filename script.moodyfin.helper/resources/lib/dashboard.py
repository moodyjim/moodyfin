"""MoodyFin dashboard (window 1153): the Jellyfin theme's admin dashboard home (web-src/js/19-dashboard-skin.js) and its
Now Playing panel (24-now-playing.js), read from the Jellyfin server with the Jellyfin add-on's login.

The service calls Dashboard.tick() four times a second; it only asks the server while the dashboard is open, on the
theme's schedule (sessions / upload / CPU every 5 s, activity 15 s, server + storage 60 s, library 5 min, users 30 min;
tasks every 2.5 s while one runs). Everything lands on Window(Home):

    MoodyFin.Dash.Name / Version / Theme / Update / Restart     server bar (Update, Restart = "1" when true)
    MoodyFin.Dash.Uptime / Cpu / Memory / Transcoding / Devices / Users
    MoodyFin.Dash.Streams / DP / DS / RM / TC / Paused            Now Playing bar (counts)
    MoodyFin.Dash.UpStreams / UpTotal                             Mbps (theme plugin's meter)
    MoodyFin.Dash.Movies / Series / Episodes / Collections (+ .New)  library strip
    MoodyFin.Dash.Scan                                            "37%" while a library scan runs
    MoodyFin.Dash.np.<1-6>.<key>                                  Now Playing cards (NP_KEYS)
    MoodyFin.Dash.<list> + MoodyFin.Dash.<list>.Reload            JSON for the plugin rows (act, sto, task, att, rec)

The rows: plugin://script.moodyfin.helper/?row=dash&part=act|sto|task|att|rec&reload=... (rows() below).
"""
import datetime
import hashlib
import json
import threading
import time
from urllib.parse import urlencode

import xbmc
import xbmcgui

from . import jellyfin

HOME = xbmcgui.Window(10000)
P = "MoodyFin.Dash."
WINDOW = "Window.IsActive(1153)"
NP_SLOTS = 6
NP_KEYS = ("title", "sub", "poster", "bg", "user", "dev", "av", "initial", "m", "edge", "pill", "summary", "conv",
           "mbps", "pct", "time")
THEME_ID = "01c723cc-57de-4e19-b13c-514b644491a5"   # the Jellyfin theme plugin's id (public, from the theme)
DAY = 86400

LABEL = {"dp": "Direct Play", "ds": "Direct Stream", "rm": "Remux", "tc": "Transcode"}
CODEC = {"h264": "H.264", "hevc": "HEVC", "h265": "HEVC", "av1": "AV1", "vp9": "VP9", "mpeg2video": "MPEG-2"}
FOLDERS = [("ProgramDataFolder", "Program data"), ("CacheFolder", "Cache"), ("ImageCacheFolder", "Image cache"),
           ("InternalMetadataFolder", "Metadata"), ("LogFolder", "Logs"), ("TranscodingTempFolder", "Transcodes"),
           ("WebFolder", "Web")]


# ---------------------------------------------------------------- formatting (as the theme's)
def _num(n):
    return "{:,}".format(int(n or 0))


def _bytes(b):
    if b is None or b < 0:
        return "?"
    units, i = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"], 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024.0
        i += 1
    return ("%.1f" if i >= 3 else "%.0f") % b + " " + units[i]


def _parse(iso):
    try:
        return datetime.datetime.fromisoformat(str(iso)[:19]).replace(tzinfo=datetime.timezone.utc).astimezone()
    except ValueError:
        return None


def _hhmm(d):
    return d.strftime("%I:%M %p").lstrip("0")


def _when(iso):
    d = _parse(iso)
    if not d:
        return ""
    if d.date() == datetime.date.today():
        return d.strftime("%I:%M %p")             # 2-digit hour, like the theme's
    return d.strftime("%a %I:%M %p")


def _up_for(m):
    if m is None or m < 0:
        return "–"
    d, h = m // 1440, m % 1440 // 60
    return "%dd %dh" % (d, h) if d else "%dh %dm" % (h, m % 60) if h else "%dm" % m


def _clock(ticks):
    s = max(0, int((ticks or 0) / 1e7))
    h, m, x = s // 3600, s % 3600 // 60, s % 60
    return ("%d:%02d:%02d" % (h, m, x)) if h else ("%d:%02d" % (m, x))


def _eta(remain_ticks):
    d = datetime.datetime.now() + datetime.timedelta(seconds=remain_ticks / 1e7)
    return _hhmm(d)


def _mb(v):
    if v is None:
        return "–"
    return str(int(round(v))) if v >= 100 else "%.1f" % v


def _res(w, h):
    w, h = w or 0, h or 0
    if not w:
        return ""
    if w >= 3200 or h >= 1800:
        return "4K"
    if w >= 1800 or h >= 1000:
        return "1080p"
    if w >= 1200 or h >= 700:
        return "720p"
    return "%dp" % (h or w)


def _codec(c):
    c = str(c or "").lower()
    return CODEC.get(c, c.upper())


def _q(path, **params):
    return path + "?" + urlencode({k: v for k, v in params.items() if v is not None})


# ---------------------------------------------------------------- the dashboard
class Dashboard:
    def __init__(self):
        self.due = {}
        self.busy = False
        self.cpu = None
        self.users = {}
        self.rates = {}
        self.sessions = []
        self.address = ""
        self.scan_at = 0
        self.tasks = []
        self.failed = []
        self.drives = []

    def tick(self):
        if not xbmc.getCondVisibility(WINDOW):
            if self.due:
                self.due = {}       # next open loads everything at once
            return
        if self.busy:
            return
        now = time.time()
        jobs = []
        running = HOME.getProperty(P + "TaskRunning") == "1"
        for name, every in (("sys", 60), ("users", 1800), ("proc", 5), ("sessions", 5), ("meter", 5),
                            ("tasks", 2.5 if running else 5), ("log", 15), ("storage", 60), ("library", 300)):
            if now >= self.due.get(name, 0):
                self.due[name] = now + every
                jobs.append(name)
        if jobs:
            self.busy = True
            threading.Thread(target=self._run, args=(jobs,), daemon=True).start()

    def _run(self, jobs):
        try:
            self.address = jellyfin._login()[0]
            for name in jobs:
                try:
                    getattr(self, "_" + name)()
                except jellyfin.JellyfinError:
                    pass
                except Exception as exc:  # one broken part must not stop the others
                    xbmc.log("[moodyfin] dashboard %s: %r" % (name, exc), xbmc.LOGWARNING)
        except jellyfin.JellyfinError:
            HOME.setProperty(P + "Name", "Jellyfin isn't reachable")
        finally:
            self.busy = False

    def _img(self, iid, kind, tag, **opts):
        if not iid or not tag:
            return ""
        opts.update(tag=tag, quality=opts.get("quality", 90))
        return _q("%s/Items/%s/Images/%s" % (self.address, iid, kind), **opts)

    def _user_pic(self, uid, tag, size=64):
        return _q("%s/Users/%s/Images/Primary" % (self.address, uid), tag=tag, maxWidth=size, quality=90) if tag else ""

    @staticmethod
    def _list(name, data):
        raw = json.dumps(data, separators=(",", ":"))
        if HOME.getProperty(P + name) != raw:
            HOME.setProperty(P + name, raw)
            HOME.setProperty(P + name + ".Reload", hashlib.md5(raw.encode()).hexdigest()[:10])

    # -- server
    def _sys(self):
        i = jellyfin.call("GET", "/System/Info") or {}
        HOME.setProperty(P + "Name", i.get("ServerName") or "Jellyfin")
        HOME.setProperty(P + "Version", i.get("Version") or "")
        HOME.setProperty(P + "Update", "1" if i.get("HasUpdateAvailable") else "")
        HOME.setProperty(P + "Restart", "1" if i.get("HasPendingRestart") else "")
        for p in jellyfin.call("GET", "/Plugins") or []:
            if str(p.get("Id", "")).replace("-", "") == THEME_ID.replace("-", ""):
                v = str(p.get("Version") or "")
                HOME.setProperty(P + "Theme", v[:-2] if v.endswith(".0") else v)

    def _users(self):
        users = jellyfin.call("GET", "/Users") or []
        self.users = {u.get("Id"): u for u in users}
        HOME.setProperty(P + "Users", _num(len(users)))

    def _proc(self):
        p = jellyfin.call("GET", "/<theme plugin>/Meter/Process") or {}
        if p.get("cpuPercent") is not None:
            HOME.setProperty(P + "Cpu", "%d%%" % round(p["cpuPercent"]))
        mem = p.get("memoryMb")
        if mem:
            HOME.setProperty(P + "Memory", "%.1f GB" % (mem / 1024.0) if mem >= 1024 else "%d MB" % mem)
        HOME.setProperty(P + "Uptime", _up_for(p.get("uptimeMinutes")))
        if self.cpu is None:            # the CPU figure needs two readings
            self.cpu = True
            self.due["proc"] = time.time() + 2.5

    # -- now playing
    def _meter(self):
        r = jellyfin.call("GET", _q("/<theme plugin>/Meter", seconds=10, streamSeconds=30)) or {}
        HOME.setProperty(P + "UpTotal", _mb(r.get("totalMbps")))
        HOME.setProperty(P + "UpStreams", _mb(r.get("streamsMbps")))
        self.rates = r.get("perStream") or {}

    @staticmethod
    def _method(s):
        ps, ti = s.get("PlayState") or {}, s.get("TranscodingInfo")
        if ps.get("PlayMethod") == "Transcode" and ti:
            return "rm" if ti.get("IsVideoDirect") and ti.get("IsAudioDirect") else "tc"
        return "ds" if ps.get("PlayMethod") == "DirectStream" else "dp"

    def _rate(self, s, counts):
        ps, it = s.get("PlayState") or {}, s.get("NowPlayingItem") or {}
        keys = []
        if ps.get("PlaySessionId"):
            keys.append("ps:" + ps["PlaySessionId"])
        if s.get("DeviceId"):
            keys.append("dev:" + s["DeviceId"])
        if it.get("Id") and counts.get(it["Id"]) == 1:
            keys.append("item:" + str(it["Id"]).replace("-", "").lower())
        for k in keys:
            if (self.rates.get(k) or 0) > 0.05:
                return _mb(self.rates[k]) + " Mbps"
        if not self.rates:
            return "–"
        return "Paused" if ps.get("IsPaused") else "0.0 Mbps"

    def _sessions(self):
        sessions = jellyfin.call("GET", _q("/Sessions", ActiveWithinSeconds=960)) or []
        self.sessions = sessions
        playing = [s for s in sessions if s.get("NowPlayingItem")]
        playing.sort(key=lambda s: ((s.get("UserName") or "").lower(), (s.get("DeviceName") or "").lower()))
        counts = {}
        for s in playing:
            counts[s["NowPlayingItem"].get("Id")] = counts.get(s["NowPlayingItem"].get("Id"), 0) + 1
        c = {"dp": 0, "ds": 0, "rm": 0, "tc": 0}
        paused = 0
        cards = []
        for s in playing:
            m = self._method(s)
            c[m] += 1
            it, ps, ti = s["NowPlayingItem"], s.get("PlayState") or {}, s.get("TranscodingInfo") or {}
            is_paused = bool(ps.get("IsPaused"))
            paused += is_paused
            ep = it.get("Type") == "Episode"
            poster = (self._img(it.get("SeriesId"), "Primary", it.get("SeriesPrimaryImageTag"), maxHeight=360) if ep else "") \
                or self._img(it.get("Id"), "Primary", (it.get("ImageTags") or {}).get("Primary"), maxHeight=360)
            bg = self._img(it.get("SeriesId") if ep else it.get("Id"), "Backdrop",
                           ((it.get("ParentBackdropImageTags") if ep else it.get("BackdropImageTags")) or [None])[0],
                           maxWidth=24, quality=60)
            title = (it.get("SeriesName") or it.get("Name")) if ep else it.get("Name")
            sub = ("S%d:E%d • %s" % (it.get("ParentIndexNumber") or 0, it.get("IndexNumber") or 0, it.get("Name") or "")
                   if ep else str(it.get("ProductionYear") or ""))
            video = next((x for x in it.get("MediaStreams") or [] if x.get("Type") == "Video"), {})
            vrt = video.get("VideoRangeType") or ""
            hdr = video.get("VideoRange") == "HDR" or any(k in vrt.upper() for k in ("HDR", "DOVI", "HLG"))
            hdr_name = ("Dolby Vision" if "DOVI" in vrt.upper() else "HDR10+" if "HDR10PLUS" in vrt.upper()
                        else "HLG" if "HLG" in vrt.upper() else "HDR" if hdr else "")
            conv = bool(ti) and not ti.get("IsVideoDirect")
            src = " ".join(x for x in (_res(video.get("Width"), video.get("Height")), hdr_name, _codec(video.get("Codec"))) if x)
            out = " ".join(x for x in (_res(ti.get("Width"), ti.get("Height")), _codec(ti.get("VideoCodec"))) if x) if conv else ""
            run, pos = it.get("RunTimeTicks") or 0, ps.get("PositionTicks") or 0
            cards.append({
                "title": title or "", "sub": sub, "poster": poster, "bg": bg,
                "user": s.get("UserName") or "", "dev": "%s · %s" % (s.get("Client") or "", s.get("DeviceName") or ""),
                "av": self._user_pic(s.get("UserId"), s.get("UserPrimaryImageTag"), 128),
                "initial": (s.get("UserName") or "?")[:1].upper(),
                "m": "pa" if is_paused else m, "edge": "pa" if is_paused else ("ds" if m == "rm" else m),
                "pill": LABEL[m],
                "summary": src + (" › " + out if conv and out else ""), "conv": "1" if conv else "",
                "mbps": self._rate(s, counts),
                "pos": int(pos / 1e7), "run": int(run / 1e7),
                "time": "%s / %s · ends %s" % (_clock(pos), _clock(run), _eta(max(0, run - pos))),
            })
        tc = sum(1 for s in playing if (s.get("PlayState") or {}).get("PlayMethod") == "Transcode" and s.get("TranscodingInfo")
                 and not (s["TranscodingInfo"].get("IsVideoDirect") and s["TranscodingInfo"].get("IsAudioDirect")))
        HOME.setProperty(P + "Streams", str(len(playing)))
        for k in c:
            HOME.setProperty(P + k.upper(), str(c[k]))
        HOME.setProperty(P + "Paused", str(paused))
        HOME.setProperty(P + "Transcoding", str(tc))
        HOME.setProperty(P + "Devices", str(len(sessions)))
        # six card slots (np.1 ... np.6): the skin lays them out itself (a list can't hold its grouplists)
        for n in range(1, NP_SLOTS + 1):
            card = cards[n - 1] if n <= len(cards) else {}
            for k in NP_KEYS:
                v = card.get(k, "")
                if k == "pct":
                    v = str(int(card["pos"] * 100 / card["run"])) if card and card.get("run") else ("0" if card else "")
                HOME.setProperty("%snp.%d.%s" % (P, n, k), str(v))

    # -- tasks, activity, storage, library
    def _tasks(self):
        tasks = jellyfin.call("GET", _q("/ScheduledTasks", isHidden="false")) or []
        run = [t for t in tasks if t.get("State") == "Running"]
        HOME.setProperty(P + "TaskRunning", "1" if run else "")
        scan = next((t for t in run if t.get("Key") == "RefreshLibrary"), None)
        if scan:
            HOME.setProperty(P + "Scan", "%d%%" % max(0, min(100, round(scan.get("CurrentProgressPercentage") or 0))))
        elif time.time() - self.scan_at > 8:
            HOME.setProperty(P + "Scan", "")
        rows = [{"name": t.get("Name") or "", "pct": max(0, min(100, round(t.get("CurrentProgressPercentage") or 0)))}
                for t in run]
        lib = next((t for t in tasks if t.get("Key") == "RefreshLibrary"), {})
        last = (lib.get("LastExecutionResult") or {}).get("EndTimeUtc")
        HOME.setProperty(P + "Idle", "Nothing running" + (" · last library scan " + _when(last) if last else ""))
        self._list("task", rows)
        self.tasks = tasks
        self._attention()

    def _log(self):
        since = (datetime.datetime.utcnow() - datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        log = (jellyfin.call("GET", _q("/System/ActivityLog/Entries", startIndex=0, limit=60, minDate=since)) or {}).get("Items") or []
        week = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        failed = (jellyfin.call("GET", _q("/System/ActivityLog/Entries", startIndex=0, limit=200, minDate=week,
                                          hasUserId="false")) or {}).get("Items") or []
        self.failed = [e for e in failed if e.get("Type") == "AuthenticationFailed"]
        groups, rows = {}, []
        for e in log:
            name = (e.get("Name") or "").strip()
            words = name.split(" ")
            if len(words) > 1 and words[-1] == words[-2]:      # "from iPhone iPhone" -> "from iPhone"
                name = " ".join(words[:-1])
            if name in groups:
                groups[name]["n"] += 1
                continue
            groups[name] = {"e": e, "name": name, "n": 1}
            rows.append(groups[name])
        out = []
        for r in rows[:20]:
            e, name = r["e"], r["name"]
            color, glyph = _kind(e.get("Type"))
            uid = e.get("UserId") or ""
            u = self.users.get(uid) if uid and uid.strip("0-") else None
            text = name.replace("[", "(").replace("]", ")")
            if u and u.get("Name") and name.startswith(u["Name"]):
                text = "[B]%s[/B]%s" % (u["Name"], text[len(u["Name"]):])
            out.append({"time": _when(e.get("Date")), "text": text, "color": color, "glyph": glyph,
                        "pic": self._user_pic(u.get("Id"), u.get("PrimaryImageTag")) if u else "",
                        "n": "×%d" % r["n"] if r["n"] > 1 else "", "nw": str(len(str(r["n"]))) if r["n"] > 1 else "",
                        "red": "1" if glyph == "alert" else ""})
        self._list("act", out)
        self._attention()

    def _storage(self):
        s = jellyfin.call("GET", "/System/Info/Storage") or {}
        self.drives = _drives(s)
        rows = []
        for g in self.drives:
            pct = min(100, round(g["used"] / g["total"] * 100)) if g["total"] > 0 else 0
            rows.append({"title": g["title"], "pct": pct, "color": "FFFF4D6D" if pct >= 95 else "FFFFB347" if pct >= 85 else "FF3EE0A1",
                         "size": "%s / %s · " % (_bytes(g["used"]), _bytes(g["total"])),
                         "free": "%s free" % _bytes(g["total"] - g["used"]),
                         "summary": "%d%% used · %d %s" % (pct, len(g["items"]), "folder" if len(g["items"]) == 1 else "folders")})
        self._list("sto", rows)
        self._attention()

    def _library(self):
        uid = jellyfin._login()[1]
        c = jellyfin.call("GET", _q("/Items/Counts", userId=uid)) or {}
        r = jellyfin.call("GET", _q("/Users/%s/Items" % uid, IncludeItemTypes="Movie,Series,Episode,BoxSet", Recursive="true",
                                    SortBy="DateCreated", SortOrder="Descending", Limit=500, Fields="DateCreated",
                                    EnableImages="false", EnableUserData="false", EnableTotalRecordCount="false")) or {}
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        new = {}
        for it in r.get("Items") or []:
            d = _parse(it.get("DateCreated"))
            if d and d >= since:
                new[it.get("Type")] = new.get(it.get("Type"), 0) + 1
        for label, key, kind in (("Movies", "MovieCount", "Movie"), ("Series", "SeriesCount", "Series"),
                                 ("Episodes", "EpisodeCount", "Episode"), ("Collections", "BoxSetCount", "BoxSet")):
            HOME.setProperty(P + label, _num(c.get(key)))
            HOME.setProperty(P + label + ".New", "+%d" % new[kind] if new.get(kind) else "")
        latest = jellyfin.call("GET", _q("/Users/%s/Items/Latest" % uid, Limit=16, Fields="PrimaryImageAspectRatio,ProductionYear",
                                         ImageTypeLimit=1, EnableImageTypes="Primary", EnableUserData="false")) or []
        ids = _kodi_ids([it.get("Id") for it in latest])
        rec = []
        for it in latest:
            iid, tag = it.get("Id"), (it.get("ImageTags") or {}).get("Primary")
            if not tag and it.get("SeriesId") and it.get("SeriesPrimaryImageTag"):
                iid, tag = it["SeriesId"], it["SeriesPrimaryImageTag"]
            sub = ("%d new" % it["ChildCount"]) if (it.get("ChildCount") or 0) > 1 else str(it.get("ProductionYear") or it.get("Type") or "")
            kind, dbid = ids.get(str(it.get("Id") or "").replace("-", ""), ("", 0))
            rec.append({"name": it.get("SeriesName") or it.get("Name") or "", "sub": sub,
                        "poster": self._img(iid, "Primary", tag, maxHeight=330), "kind": kind, "dbid": dbid})
        self._list("rec", rec)

    def _attention(self):
        items = []
        failed = getattr(self, "failed", None) or []
        if failed:
            by, order = {}, []
            for e in failed:
                name = e.get("Name") or ""
                n = name.rsplit(" from ", 1)[1].strip() if " from " in name else name or "?"
                if n not in by:
                    by[n] = 0
                    order.append(n)
                by[n] += 1
            order.sort(key=lambda n: -by[n])
            s = " · ".join("%s ×%d" % (n, by[n]) for n in order[:4]) + (" · +%d more" % (len(order) - 4) if len(order) > 4 else "")
            items.append({"c": "FFFF5D73", "i": "!", "red": "1", "t": "%d failed login%s this week" % (len(failed), "" if len(failed) == 1 else "s"),
                          "s": s + " · last " + _when(failed[0].get("Date"))})
        for g in getattr(self, "drives", None) or []:
            pct = round(g["used"] / g["total"] * 100) if g["total"] > 0 else 0
            if pct >= 85:
                items.append({"c": "FFFF5D73" if pct >= 95 else "FFFFB347", "i": "", "icon": "storage", "red": "1" if pct >= 95 else "",
                              "t": "%s is %d%% full" % (g["title"], pct), "s": "%s free · %s" % (_bytes(g["total"] - g["used"]), g["dir"])})
        if HOME.getProperty(P + "Restart"):
            items.append({"c": "FFFFB347", "i": "", "icon": "restart_alt", "red": "", "t": "Restart pending",
                          "s": "Something was installed or changed; it takes effect after a restart (Server menu)"})
        if HOME.getProperty(P + "Update"):
            items.append({"c": "mf_accent", "i": "", "icon": "arrow_upward", "red": "", "t": "Jellyfin update available", "s": "A newer server version is out"})
        for t in getattr(self, "tasks", None) or []:
            r = t.get("LastExecutionResult") or {}
            end = _parse(r.get("EndTimeUtc"))
            if r.get("Status") == "Failed" and end and (datetime.datetime.now(datetime.timezone.utc) - end).total_seconds() < DAY:
                items.append({"c": "FFFF5D73", "i": "×", "red": "1", "t": "Task failed: " + (t.get("Name") or ""),
                              "s": (r.get("ErrorMessage") or "See the task's log") + " · " + _when(r.get("EndTimeUtc"))})
        self._list("att", items[:4])


def _kind(t):
    t = t or ""
    if any(k in t for k in ("AuthenticationFailed", "LockedOut", "UserDeleted")):
        return "FFFF5D73", "alert"
    if "Playback" in t:
        return "mf_accent", "play"
    if "SessionEnded" in t:
        return "FF8A8F98", "ring"
    if any(k in t for k in ("AuthenticationSucceeded", "SessionStarted", "UserCreated")):
        return "FF3EE0A1", "dot"
    if any(k in t for k in ("Plugin", "Update", "Install")):
        return "FFB98BFF", "spark"
    if any(k in t for k in ("Password", "Policy", "Configuration")):
        return "FFFF9F43", "gear"
    return "FF4FC3FF", "dot"


def _common_dir(paths):
    parts = [p.replace("\\", "/").split("/") for p in paths]
    if not parts:
        return ""
    out = []
    for i, seg in enumerate(parts[0]):
        if all(len(p) > i and p[i] == seg for p in parts):
            out.append(seg)
        else:
            break
    return "/".join(out) or "/"


def _drives(s):
    """the Jellyfin theme's groupDrives(): folders grouped by the drive they're on."""
    groups, order = {}, []

    def add(label, f, lib):
        if not f or not f.get("Path") or (f.get("UsedSpace") or -1) < 0:
            return
        free = max(f.get("FreeSpace") or 0, 0)
        k = f.get("DeviceId") or "u%sf%s" % (f["UsedSpace"], free)
        g = groups.get(k)
        if not g:
            g = groups[k] = {"used": f["UsedSpace"], "total": f["UsedSpace"] + free, "items": [], "paths": set(),
                             "system": False, "lib": False}
            order.append(g)
        if label == "Program data":
            g["system"] = True
        if lib:
            g["lib"] = True
        if f["Path"] in g["paths"]:
            return
        g["paths"].add(f["Path"])
        g["items"].append({"label": label, "path": f["Path"]})

    for key, label in FOLDERS:
        add(label, s.get(key), False)
    for lib in s.get("Libraries") or []:
        for f in lib.get("Folders") or []:
            add(lib.get("Name"), f, True)
    order.sort(key=lambda g: (-g["system"], -g["total"]))
    media = 0
    for g in order:
        g["dir"] = _common_dir([i["path"] for i in g["items"]])
        g["title"] = "System drive" if g["system"] else "Media drive" if g["lib"] else "Storage"
        media += (not g["system"] and g["lib"])
    if media > 1:
        n = 0
        for g in order:
            if not g["system"] and g["lib"]:
                n += 1
                g["title"] = "Media drive %d" % n
    return order


def _kodi_ids(jids):
    """Jellyfin ids -> (Kodi type, dbid), from Jellyfin for Kodi's own table (read only)."""
    import sqlite3
    import xbmcvfs
    path = xbmcvfs.translatePath("special://database/jellyfin.db").replace("\\", "/")
    out = {}
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=2)
        try:
            for jid in jids:
                key = str(jid or "").replace("-", "")
                row = con.execute("SELECT media_type, kodi_id FROM jellyfin WHERE jellyfin_id = ?", (key,)).fetchone()
                if row and row[0] in ("movie", "tvshow", "episode"):
                    out[key] = (row[0], row[1])
        finally:
            con.close()
    except sqlite3.Error:
        pass
    return out


# ---------------------------------------------------------------- plugin rows
def rows(part):
    """ListItems for the dashboard's lists (row=dash&part=...), from the JSON the service left on Window(Home)."""
    try:
        data = json.loads(HOME.getProperty(P + part) or "[]")
    except ValueError:
        data = []
    out = []
    for d in data:
        li = xbmcgui.ListItem(d.get("title") or d.get("name") or d.get("text") or d.get("t") or "", offscreen=True)
        for k, v in d.items():
            li.setProperty("mf." + k, str(v))
        if part == "rec":
            li.setArt({"poster": d.get("poster", "")})
        elif part == "act":
            li.setArt({"thumb": d.get("pic", "")})
        out.append((li, False))
    return out


# ---------------------------------------------------------------- actions (buttons)
def scan():
    try:
        jellyfin.call("POST", "/Library/Refresh")
    except jellyfin.JellyfinError as e:
        xbmcgui.Dialog().notification("MoodyFin", str(e), xbmcgui.NOTIFICATION_WARNING, 4000)
        return
    HOME.setProperty(P + "Scan", "0%")
    HOME.setProperty(P + "TaskRunning", "1")


def server_menu():
    """The theme's Server menu: Restart / Shutdown, each confirmed (who is watching is said)."""
    try:
        sessions = jellyfin.call("GET", _q("/Sessions", ActiveWithinSeconds=960)) or []
    except jellyfin.JellyfinError:
        sessions = []
    w = sum(1 for s in sessions if s.get("NowPlayingItem") and not (s.get("PlayState") or {}).get("IsPaused"))
    people = "1 person is watching" if w == 1 else "%d people are watching" % w
    who = (people + ". They'll be cut off.") if w else "Nobody is watching right now."
    pick = xbmcgui.Dialog().select("Server", ["Restart", "Shutdown"])
    if pick == 0 and xbmcgui.Dialog().yesno("Restart the server", who, nolabel="Cancel", yeslabel="Restart"):
        jellyfin.call("POST", "/System/Restart")
    elif pick == 1 and xbmcgui.Dialog().yesno(
            "Shut the server down", who + " It stays off until someone starts it again on the machine.",
            nolabel="Cancel", yeslabel="Shut down"):
        jellyfin.call("POST", "/System/Shutdown")
