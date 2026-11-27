"""Plugin source for MoodyFin's Home rows: plugin://script.moodyfin.helper/?row=<name>[&reload=...]

Rows: hero, continue, top10, latest, recentmovies, recentshows; dash&part=... (the dashboard's lists, dashboard.py). `reload` is only there so the skin can make Kodi
fetch a row again (the service changes it after playback and library updates).
"""
import datetime
import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcplugin

from . import dashboard, items, rpc

SORT_LASTPLAYED = {"method": "lastplayed", "order": "descending"}
SORT_ADDED = {"method": "dateadded", "order": "descending"}
INPROGRESS = {"field": "inprogress", "operator": "true", "value": ""}
UNWATCHED = {"field": "playcount", "operator": "is", "value": "0"}
NOT_SPECIALS = {"field": "season", "operator": "greaterthan", "value": "0"}


def _today():
    return datetime.date.today().isoformat()


def continue_row(limit=30):
    """In-progress movies and episodes, and the next episode of shows being watched, newest first."""
    entries = []
    for m in rpc.movies(SORT_LASTPLAYED, limit, INPROGRESS):
        entries.append((m.get("lastplayed", ""), items.movie(m)))
    busy_shows = set()
    for e in rpc.episodes(SORT_LASTPLAYED, limit, INPROGRESS):
        busy_shows.add(e.get("tvshowid"))
        entries.append((e.get("lastplayed", ""), items.episode(e)))
    for s in rpc.shows(SORT_LASTPLAYED, 20, INPROGRESS):
        if s["tvshowid"] in busy_shows:
            continue
        nxt = rpc.episodes({"method": "episode", "order": "ascending"}, 1,
                           {"and": [UNWATCHED, NOT_SPECIALS]}, tvshowid=s["tvshowid"])
        if nxt:
            entries.append((s.get("lastplayed", ""), items.episode(nxt[0])))
    entries.sort(key=lambda x: x[0], reverse=True)
    return [li for _, li in entries[:limit]]


def top10_row():
    """Best-rated titles added lately (library stand-in for the Jellyfin theme's TMDB trending)."""
    for days in (60, 180, 730, None):
        filt = {"field": "dateadded", "operator": "inthelast", "value": "%d days" % days} if days else None
        pool = [(m.get("rating", 0), items.movie(m)) for m in rpc.movies({"method": "rating", "order": "descending"}, 10, filt)]
        pool += [(s.get("rating", 0), items.tvshow(s)) for s in rpc.shows({"method": "rating", "order": "descending"}, 10, filt)]
        if len(pool) >= 10 or days is None:
            break
    pool.sort(key=lambda x: x[0], reverse=True)
    out = []
    for rank, (_, entry) in enumerate(pool[:10], 1):
        entry[0].setProperty("mf.rank", str(rank))
        out.append(entry)
    return out


def latest_row(limit=16):
    """Newest releases (already out), movies and shows together."""
    today = _today()
    pool = [(m.get("premiered", ""), items.movie(m)) for m in rpc.movies({"method": "year", "order": "descending"}, 60)]
    pool += [(s.get("premiered", ""), items.tvshow(s)) for s in rpc.shows({"method": "year", "order": "descending"}, 30)]
    pool = [p for p in pool if p[0] and p[0] <= today]
    pool.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in pool[:limit]]


def recentmovies_row(limit=16):
    return [items.movie(m) for m in rpc.movies(SORT_ADDED, limit)]


def _recent_show_ids(limit):
    """Shows in the order their newest episode was added, and which of them just got a new season."""
    order, new_season = [], set()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    for e in rpc.episodes(SORT_ADDED, 300):
        sid = e.get("tvshowid")
        if sid not in order:
            order.append(sid)
        if e.get("episode") == 1 and e.get("season", 0) > 1 and e.get("dateadded", "") >= cutoff:
            new_season.add(sid)
        if len(order) > limit:
            break
    return order[:limit], new_season


def recentshows_row(limit=16):
    out = []
    ids, new_season = _recent_show_ids(limit)
    for sid in ids:
        d = rpc.show(sid)
        if not d:
            continue
        entry = items.tvshow(d)
        if sid in new_season:
            entry[0].setProperty("mf.tag", "New season")
        out.append(entry)
    return out


def hero_row(limit=8):
    """Recently added, unwatched, with a backdrop (the title logo is optional: the skin writes the title)."""
    def ok(d):
        return (d.get("art") or {}).get("fanart")
    movies = [items.movie(m) for m in rpc.movies(SORT_ADDED, 40, UNWATCHED) if ok(m)][:limit - 2]
    shows = []
    ids, _ = _recent_show_ids(10)
    for sid in ids:
        d = rpc.show(sid)
        if d and ok(d):
            shows.append(items.tvshow(d))
        if len(shows) >= 2:
            break
    out = []
    while movies or shows:  # 3 movies, 1 show, ...
        out += movies[:3]
        movies = movies[3:]
        if shows:
            out.append(shows.pop(0))
    return out[:limit]


def _top10(params):
    out = top10_row()
    part = params.get("part")
    if part == "first":
        return out[:1]
    if part == "rest":
        return out[1:]
    return out


def nextup_row(params):
    """The next episode to watch for one show: the in-progress one, else the first unwatched."""
    sid = int(params.get("tvshowid", 0) or 0)
    if not sid:
        return []
    eps = rpc.episodes(SORT_LASTPLAYED, 1, INPROGRESS, tvshowid=sid)
    if not eps:
        eps = rpc.episodes({"method": "episode", "order": "ascending"}, 1, {"and": [UNWATCHED, NOT_SPECIALS]}, tvshowid=sid)
    return [items.episode(e) for e in eps]


def seasons_row(params):
    sid = int(params.get("tvshowid", 0) or 0)
    return [items.season(d, sid) for d in rpc.seasons(sid) if d.get("season", 0) > 0] if sid else []


def collection_row(params):
    setid = int(params.get("setid", 0) or 0)
    d = rpc.movie_set(setid) if setid else None
    return [items.movieset(d)] if d else []


def similar_row(params, limit=16):
    """Same first two genres, best rated first (fallback when plugin.video.moodysimilar isn't there)."""
    kind, dbid = params.get("type", "movie"), int(params.get("dbid", 0) or 0)
    if kind not in ("movie", "tvshow") or not dbid:
        return []
    d = rpc.details(kind, dbid) or {}
    genres = (d.get("genre") or [])[:2]
    if not genres:
        return []
    filt = {"and": [{"field": "genre", "operator": "is", "value": g} for g in genres]}
    sort = {"method": "rating", "order": "descending"}
    if kind == "movie":
        found = [items.movie(m) for m in rpc.movies(sort, limit + 1, filt) if m["movieid"] != dbid]
    else:
        found = [items.tvshow(t) for t in rpc.shows(sort, limit + 1, filt) if t["tvshowid"] != dbid]
    return found[:limit]


def search_row(params, limit=40):
    """Titles containing the query: type=movie|tvshow|episode."""
    q = (params.get("q") or "").strip()
    kind = params.get("type", "movie")
    if len(q) < 2:
        return []
    filt = {"field": "title", "operator": "contains", "value": q}
    sort = {"method": "title", "order": "ascending", "ignorearticle": True}
    if kind == "movie":
        return [items.movie(m) for m in rpc.movies(sort, limit, filt)]
    if kind == "tvshow":
        return [items.tvshow(t) for t in rpc.shows(sort, limit, filt)]
    if kind == "episode":
        return [items.episode(e) for e in rpc.episodes({"method": "lastplayed", "order": "descending"}, limit, filt)]
    return []


EPISODE_DAYS = 7    # "New episode": aired in the last week (the Jellyfin theme's 08-new-episode-tags.js)
SEASON_DAYS = 28    # "New season": a season premiere (S2+ E1) aired in the last four weeks


def new_tags():
    """tvshowid -> "New season" / "New episode", from the newest episodes (air date, else date added)."""
    today = datetime.date.today()
    tags = {}
    for e in rpc.episodes(SORT_ADDED, 400):
        day = (e.get("firstaired") or e.get("dateadded") or "")[:10]
        try:
            age = (today - datetime.date.fromisoformat(day)).days
        except ValueError:
            continue
        sid = e.get("tvshowid")
        if e.get("season", 0) > 1 and e.get("episode") == 1 and 0 <= age <= SEASON_DAYS:
            tags[sid] = "New season"
        elif 0 <= age <= EPISODE_DAYS and tags.get(sid) != "New season":
            tags[sid] = "New episode"
    return tags


def _plain(fn):
    return lambda params: fn()


ROWS = {"hero": _plain(hero_row), "continue": _plain(continue_row), "top10": _top10, "latest": _plain(latest_row),
        "recentmovies": _plain(recentmovies_row), "recentshows": _plain(recentshows_row), "nextup": nextup_row,
        "seasons": seasons_row, "collection": collection_row, "similar": similar_row,
        "search": search_row, "dash": lambda params: dashboard.rows(params.get("part", ""))}


def run(argv):
    handle = int(argv[1])
    params = dict(parse_qsl(argv[2][1:] if len(argv) > 2 else ""))
    row = ROWS.get(params.get("row", ""))
    entries = []
    if row:
        try:
            entries = row(params)
            if any(li.getProperty("mf.type") == "tvshow" for li, _ in entries):
                tags = new_tags()
                for li, _ in entries:
                    if li.getProperty("mf.type") == "tvshow":
                        li.setProperty("mf.tag", tags.get(li.getVideoInfoTag().getDbId(), ""))
        except Exception as exc:  # a broken row must not take Home down
            xbmc.log("[moodyfin] row %s failed: %r" % (params.get("row"), exc), xbmc.LOGERROR)
    xbmcplugin.setContent(handle, "videos")
    xbmcplugin.addDirectoryItems(handle, [(li.getPath(), li, folder) for li, folder in entries], len(entries))
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
