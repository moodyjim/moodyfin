"""JSON-RPC calls into Kodi's own library."""
import json

import xbmc


def call(method, params=None):
    req = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        req["params"] = params
    res = json.loads(xbmc.executeJSONRPC(json.dumps(req)))
    if "error" in res:
        xbmc.log("[moodyfin] %s failed: %s" % (method, res["error"]), xbmc.LOGWARNING)
        return {}
    return res.get("result", {})


MOVIE_PROPS = ["title", "year", "rating", "genre", "plot", "runtime", "playcount", "resume", "lastplayed",
               "dateadded", "premiered", "mpaa", "file", "art", "streamdetails", "studio", "tagline"]
SHOW_PROPS = ["title", "year", "rating", "genre", "plot", "playcount", "lastplayed", "dateadded", "premiered",
              "mpaa", "file", "art", "studio", "episode", "watchedepisodes", "season"]
EPISODE_PROPS = ["title", "showtitle", "season", "episode", "tvshowid", "rating", "plot", "runtime", "playcount",
                 "resume", "lastplayed", "dateadded", "firstaired", "file", "art", "streamdetails"]


def movies(sort, limit, filt=None):
    p = {"properties": MOVIE_PROPS, "sort": sort, "limits": {"start": 0, "end": limit}}
    if filt:
        p["filter"] = filt
    return call("VideoLibrary.GetMovies", p).get("movies", [])


def shows(sort, limit, filt=None):
    p = {"properties": SHOW_PROPS, "sort": sort, "limits": {"start": 0, "end": limit}}
    if filt:
        p["filter"] = filt
    return call("VideoLibrary.GetTVShows", p).get("tvshows", [])


def episodes(sort, limit, filt=None, tvshowid=None):
    p = {"properties": EPISODE_PROPS, "sort": sort, "limits": {"start": 0, "end": limit}}
    if filt:
        p["filter"] = filt
    if tvshowid is not None:
        p["tvshowid"] = tvshowid
    return call("VideoLibrary.GetEpisodes", p).get("episodes", [])


def show(tvshowid):
    return call("VideoLibrary.GetTVShowDetails", {"tvshowid": tvshowid, "properties": SHOW_PROPS}).get("tvshowdetails")


def count(method, key, filt=None):
    p = {"limits": {"start": 0, "end": 1}}
    if filt:
        p["filter"] = filt
    return call(method, p).get("limits", {}).get("total", 0)
