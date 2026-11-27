"""Ambient background: a soft, blurred copy of the picture on screen (the Jellyfin theme's ue-ambient).

The skin puts the picture it wants blurred in a hidden label, id 9990, on any window that shows the ambient
background. This module watches that label, makes a small blurred JPEG of the picture and sets
Window(Home).Property(MoodyFin.Ambient) to it. Without Pillow the property is the picture itself (the skin dims it).

Cheap on purpose, for ARM boxes: Jellyfin pictures are fetched at 320 px wide, JPEGs are decoded at 1/8 scale,
blurred at 160x90, and saved at 480x270 (the skin stretches it; it's a blur anyway).
"""
import hashlib
import io
import os
import threading
import urllib.request
from urllib.parse import urlsplit, urlunsplit

import xbmc
import xbmcgui
import xbmcvfs

try:
    from PIL import Image, ImageFilter
except ImportError:  # script.module.pil missing
    Image = None

HOME = xbmcgui.Window(10000)
CACHE = xbmcvfs.translatePath("special://profile/addon_data/script.moodyfin.helper/ambient/")
KEEP = 300  # blurred files kept on disk


def _small_url(url):
    """Ask Jellyfin for a small copy of its pictures (…/Items/<id>/Images/<type>…)."""
    if "/Images/" not in url:
        return url
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "maxWidth=320&quality=70", ""))


def _read(url):
    if url.startswith(("http://", "https://")):
        with urllib.request.urlopen(_small_url(url), timeout=8) as resp:
            return resp.read()
    # anything else: Kodi's own cached copy of the picture, or the file itself
    cached = xbmc.getCacheThumbName(url)
    for ext in (".jpg", ".png"):
        path = "special://thumbnails/%s/%s" % (cached[0], cached[:-4] + ext)
        if xbmcvfs.exists(path):
            url = path
            break
    f = xbmcvfs.File(url)
    try:
        return bytes(f.readBytes())
    finally:
        f.close()


def _blur(data, out):
    img = Image.open(io.BytesIO(data))
    img.draft("RGB", (240, 135))  # JPEG: decode at a fraction of the size
    img = img.convert("RGB")
    # cover 16:9
    w, h = img.size
    target = 16 / 9
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        img = img.crop((0, max(0, (h - nh) // 3), w, max(0, (h - nh) // 3) + nh))
    img = img.resize((160, 90), Image.BILINEAR).filter(ImageFilter.GaussianBlur(7))
    img = img.resize((480, 270), Image.BILINEAR)
    img.save(out, "JPEG", quality=82)


def _prune():
    try:
        files = [os.path.join(CACHE, f) for f in os.listdir(CACHE)]
        if len(files) > KEEP:
            files.sort(key=os.path.getmtime)
            for f in files[:len(files) - KEEP]:
                os.remove(f)
    except OSError:
        pass


class Ambient:
    def __init__(self):
        self.source = None
        self.busy = False
        self.pending = None
        os.makedirs(CACHE, exist_ok=True)
        _prune()

    def tick(self):
        if xbmc.Player().isPlayingVideo():
            return
        src = xbmc.getInfoLabel("Control.GetLabel(9990)")
        if not src or src == self.source:
            return
        self.source = src
        if self.busy:
            self.pending = src  # only the latest one matters
            return
        self._start(src)

    def _start(self, src):
        self.busy = True
        threading.Thread(target=self._work, args=(src,), daemon=True).start()

    def _work(self, src):
        try:
            if Image is None:
                HOME.setProperty("MoodyFin.Ambient", src)
                return
            out = os.path.join(CACHE, hashlib.md5(src.encode("utf-8")).hexdigest() + ".jpg")
            if not os.path.exists(out):
                _blur(_read(src), out)
            else:
                os.utime(out, None)
            if self.source == src or self.pending is None:
                HOME.setProperty("MoodyFin.Ambient", out)
        except Exception as exc:
            xbmc.log("[moodyfin] ambient failed for %s: %r" % (src, exc), xbmc.LOGWARNING)
        finally:
            self.busy = False
            nxt, self.pending = self.pending, None
            if nxt and nxt != src:
                self._start(nxt)

    def stop(self):
        _prune()
