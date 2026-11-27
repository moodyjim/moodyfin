"""Actions the skin runs: RunScript(script.moodyfin.helper,action=<name>,key=value,...)

    action=studio,names=Marvel Studios|Marvel Entertainment
        Opens the library filtered to those studios: movies, or shows when the studio has more shows than movies.
"""
import json
from urllib.parse import quote

import xbmc

from . import rpc


def _args(argv):
    out = {}
    for arg in argv[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def studio(names):
    names = [n for n in names.split("|") if n]
    if not names:
        return
    rule = {"or": [{"field": "studio", "operator": "is", "value": n} for n in names]}
    n_movies = rpc.count("VideoLibrary.GetMovies", "movies", rule)
    n_shows = rpc.count("VideoLibrary.GetTVShows", "tvshows", rule)
    kind, base = ("tvshows", "videodb://tvshows/titles/") if n_shows > n_movies else ("movies", "videodb://movies/titles/")
    xsp = {"rules": {"or": [{"field": "studio", "operator": "is", "value": [n]} for n in names]}, "type": kind}
    url = base + "?xsp=" + quote(json.dumps(xsp, separators=(",", ":")))
    xbmc.executebuiltin("ActivateWindow(Videos,%s,return)" % url)


def run(argv):
    args = _args(argv)
    action = args.get("action")
    if action == "studio":
        studio(args.get("names", ""))
    else:
        xbmc.log("[moodyfin] unknown action %r" % action, xbmc.LOGWARNING)
