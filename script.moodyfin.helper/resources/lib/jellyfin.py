"""Talks to the Jellyfin server as the Jellyfin for Kodi add-on's signed-in user (its saved address, user and token in
addon_data/plugin.video.jellyfin/data.json; same way as plugin.video.moodysimilar). Used for the player's favourite
button. The token is only ever sent to that server.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcvfs

JELLYFIN_ADDON = "plugin.video.jellyfin"
DATA_DIR = "special://profile/addon_data/plugin.video.jellyfin/"


class JellyfinError(Exception):
    pass


def _read(path):
    path = xbmcvfs.translatePath(path)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def _login():
    raw = _read(DATA_DIR + "data.json")
    servers = (json.loads(raw).get("Servers") or []) if raw else []
    if not servers or not servers[0].get("AccessToken"):
        raise JellyfinError("The Jellyfin add-on isn't signed in on this device.")
    s = servers[0]
    device_id = (_read(DATA_DIR + "jellyfin_guid") or "").strip() or "moodyfin"
    try:
        jf = xbmcaddon.Addon(JELLYFIN_ADDON)
        version = jf.getAddonInfo("version")
        device = jf.getSetting("deviceName") or xbmc.getInfoLabel("System.FriendlyName") or "Kodi"
    except RuntimeError:
        version, device = "0", "Kodi"
    # the Jellyfin add-on's own client / device values, so the server doesn't list a new device
    auth = 'MediaBrowser Client="Kodi", Device="%s", DeviceId="%s", Version="%s", UserId="%s", Token="%s"' % (
        urllib.parse.quote(device), device_id, version, s["UserId"], s["AccessToken"])
    return s["address"].rstrip("/"), s["UserId"], auth


def call(method, path):
    """path may contain {user}. Returns the decoded JSON ({} for an empty body)."""
    address, user_id, auth = _login()
    req = urllib.request.Request(address + path.replace("{user}", user_id), method=method,
                                 headers={"Authorization": auth, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        raise JellyfinError("Jellyfin said %d" % e.code)
    except urllib.error.URLError as e:
        raise JellyfinError("Can't reach Jellyfin (%s)" % e.reason)


def item_id(path):
    """The Jellyfin item id in a Jellyfin for Kodi file path (plugin://plugin.video.jellyfin/...?...&id=<id>&...)."""
    if not path or "plugin.video.jellyfin" not in path:
        return ""
    query = urllib.parse.urlsplit(path).query
    return dict(urllib.parse.parse_qsl(query)).get("id", "")


def is_favorite(jid):
    return bool(((call("GET", "/Users/{user}/Items/%s" % jid) or {}).get("UserData") or {}).get("IsFavorite"))


def set_favorite(jid, on):
    call("POST" if on else "DELETE", "/Users/{user}/FavoriteItems/%s" % jid)
