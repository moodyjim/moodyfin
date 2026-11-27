"""Actions the skin runs: RunScript(script.moodyfin.helper,action=<name>,key=value,...)

    action=studio,names=Marvel Studios|Marvel Entertainment
        Opens the library filtered to those studios: movies, or shows when the studio has more shows than movies.
    action=info,type=movie|tvshow|episode,dbid=N
        Opens the details page (Kodi's video info dialog) for a library item, with its whole record and cast.
        Closes an open details page first, so "More like this" can go from one title to the next.
    action=watched,type=movie|tvshow|episode,dbid=N
        Toggles watched (a show: all its episodes). Jellyfin for Kodi sends the change to the server.
        Sets Window(movieinformation).Property(mf.watched) to 1/0 so the open page updates at once.
    action=play,type=movie|episode,dbid=N
        Closes the details page and plays the item from the library, resuming where it stopped.
    action=search
        Asks for a search (Kodi's keyboard, starting from the last one) and puts it on the search page:
        Window(1150).Property(mf.query) in the skin (11150 here) to show, Property(mf.q) URL-quoted for the rows' plugin paths.
    action=playnext,tvshowid=N
        Plays the show's next episode (the one in progress, else the first unwatched), resuming where it stopped.
"""
import json
from urllib.parse import quote

import xbmc
import xbmcgui

from . import items, rpc

INFO_DIALOG = 12003


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
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    xbmc.executebuiltin("ActivateWindow(Videos,%s,return)" % url)


def info(kind, dbid):
    if kind not in ("movie", "tvshow", "episode") or not str(dbid).isdigit():
        return
    li = items.full(kind, int(dbid))
    if li is None:
        return
    if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
        xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
        monitor = xbmc.Monitor()
        for _ in range(40):
            if not xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
                break
            monitor.waitForAbort(0.05)
    xbmcgui.Dialog().info(li)


def watched(kind, dbid):
    if not str(dbid).isdigit():
        return
    dbid = int(dbid)
    if kind == "movie":
        d = rpc.call("VideoLibrary.GetMovieDetails", {"movieid": dbid, "properties": ["playcount"]}).get("moviedetails", {})
        new = 0 if d.get("playcount", 0) else 1
        rpc.call("VideoLibrary.SetMovieDetails", {"movieid": dbid, "playcount": new})
    elif kind == "episode":
        d = rpc.call("VideoLibrary.GetEpisodeDetails", {"episodeid": dbid, "properties": ["playcount"]}).get("episodedetails", {})
        new = 0 if d.get("playcount", 0) else 1
        rpc.call("VideoLibrary.SetEpisodeDetails", {"episodeid": dbid, "playcount": new})
    elif kind == "tvshow":
        d = rpc.call("VideoLibrary.GetTVShowDetails", {"tvshowid": dbid, "properties": ["episode", "watchedepisodes"]}).get("tvshowdetails", {})
        new = 0 if d.get("episode") and d.get("watchedepisodes") == d.get("episode") else 1
        for e in rpc.episodes({"method": "episode"}, 10000, tvshowid=dbid):
            if bool(e.get("playcount")) != bool(new):
                rpc.call("VideoLibrary.SetEpisodeDetails", {"episodeid": e["episodeid"], "playcount": new})
    else:
        return
    xbmcgui.Window(INFO_DIALOG).setProperty("mf.watched", str(new))


def playnext(tvshowid):
    if not str(tvshowid).isdigit():
        return
    from .rows import nextup_row
    entries = nextup_row({"tvshowid": tvshowid})
    if not entries:
        xbmcgui.Dialog().notification("MoodyFin", "Nothing left to watch", xbmcgui.NOTIFICATION_INFO, 3000)
        return
    li = entries[0][0]
    epid = li.getVideoInfoTag().getDbId()
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    rpc.call("Player.Open", {"item": {"episodeid": epid}, "options": {"resume": True}})


def play(kind, dbid):
    if kind not in ("movie", "episode") or not str(dbid).isdigit():
        return
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    rpc.call("Player.Open", {"item": {kind + "id": int(dbid)}, "options": {"resume": True}})


SEARCH_WINDOW = 11150  # custom window 1150 (Kodi adds 10000)


def search():
    win = xbmcgui.Window(SEARCH_WINDOW)
    text = xbmcgui.Dialog().input("Search movies, shows and episodes", defaultt=win.getProperty("mf.query"))
    text = (text or "").strip()
    if not text:  # Cancel also returns "": keep the last search
        return
    # Kodi doesn't reload a list inside a hidden group: keep the rows shown while the new results load
    win.setProperty("mf.searching", "1")
    win.setProperty("mf.query", text)
    win.setProperty("mf.q", quote(text))
    xbmc.Monitor().waitForAbort(4)
    win.clearProperty("mf.searching")


def run(argv):
    args = _args(argv)
    action = args.get("action")
    if action == "studio":
        studio(args.get("names", ""))
    elif action == "info":
        info(args.get("type", ""), args.get("dbid", ""))
    elif action == "watched":
        watched(args.get("type", ""), args.get("dbid", ""))
    elif action == "play":
        play(args.get("type", ""), args.get("dbid", ""))
    elif action == "search":
        search()
    elif action == "playnext":
        playnext(args.get("tvshowid", ""))
    else:
        xbmc.log("[moodyfin] unknown action %r" % action, xbmc.LOGWARNING)
