"""Library records (JSON-RPC) -> ListItems for MoodyFin's rows.

Items keep their library identity (dbid + mediatype + the library file path), so Play, resume and the info dialog
work as they do in the library. MoodyFin's own values go in ListItem.Property(mf.*):

    mf.genre   first genre            mf.rating  "7.4" (empty when unrated)
    mf.res     4K / 1080p / 720p      mf.hdr     Dolby Vision / HDR10 / HDR10+ / HLG
    mf.audio   Dolby TrueHD / Dolby Digital+ / Dolby Digital / DTS-HD / DTS
    mf.left    "36m left"             mf.sub     "S1 · E8" for episodes, the year otherwise
    mf.rank    1..10 (Top 10 row)     mf.tag     "New season" etc.
    mf.type    movie / tvshow / episode
"""
import xbmc
import xbmcgui

AUDIO = {"truehd": "Dolby TrueHD", "eac3": "Dolby Digital+", "ac3": "Dolby Digital", "dtshd_ma": "DTS-HD",
         "dtshd_hra": "DTS-HD", "dts": "DTS"}
HDR = {"dolbyvision": "Dolby Vision", "hdr10": "HDR10", "hdr10plus": "HDR10+", "hlg": "HLG"}


def _res(width, height):
    if width >= 3200 or height >= 2000:
        return "4K"
    if width >= 1800 or height >= 1000:
        return "1080p"
    if width >= 1200 or height >= 700:
        return "720p"
    return "SD" if width else ""


def _left(resume):
    pos, total = resume.get("position", 0), resume.get("total", 0)
    if not pos or not total or pos >= total:
        return ""
    mins = int((total - pos) // 60) or 1
    return "%dh %dm left" % (mins // 60, mins % 60) if mins >= 60 else "%dm left" % mins


def _rating(value):
    return "%.1f" % value if value else ""


def _streams(li, tag, sd):
    video = (sd or {}).get("video") or []
    audio = (sd or {}).get("audio") or []
    if video:
        v = video[0]
        li.setProperty("mf.res", _res(v.get("width", 0), v.get("height", 0)))
        li.setProperty("mf.hdr", HDR.get(v.get("hdrtype", ""), ""))
        tag.addVideoStream(xbmc.VideoStreamDetail(width=v.get("width", 0), height=v.get("height", 0),
                                                  codec=v.get("codec", ""), duration=v.get("duration", 0),
                                                  hdrtype=v.get("hdrtype", "")))
    if audio:
        best = next((AUDIO[a.get("codec")] for a in audio if a.get("codec") in AUDIO), "")
        li.setProperty("mf.audio", best)
        for a in audio:
            tag.addAudioStream(xbmc.AudioStreamDetail(channels=a.get("channels", 0), codec=a.get("codec", ""),
                                                      language=a.get("language", "")))
    # file name of the pre-drawn badge strip in skin media/moodyfin/badges/ (tools/build_media.sh)
    parts = [li.getProperty(k) for k in ("mf.res", "mf.hdr", "mf.audio")]
    li.setProperty("mf.badge", "_".join(p.replace(" ", "").replace("+", "plus") for p in parts if p))


def _meta(li, d, kind):
    parts = []
    if d.get("rating"):
        parts.append("[COLOR mf_star]★[/COLOR] %.1f" % d["rating"])
    if d.get("year"):
        parts.append(str(d["year"]))
    parts.append(kind)
    parts += (d.get("genre") or [])[:2]
    li.setProperty("mf.meta", "  ·  ".join(parts))


def _common(li, tag, d):
    genres = d.get("genre") or []
    li.setProperty("mf.genre", genres[0] if genres else "")
    li.setProperty("mf.genres", "  ·  ".join(genres[:2]))
    li.setProperty("mf.rating", _rating(d.get("rating", 0)))
    li.setArt(d.get("art") or {})
    tag.setTitle(d.get("title", ""))
    tag.setRating(d.get("rating", 0))
    tag.setGenres(genres)
    tag.setPlot(d.get("plot", ""))
    tag.setPlaycount(d.get("playcount", 0))
    if d.get("lastplayed"):
        tag.setLastPlayed(d["lastplayed"])
    if d.get("dateadded"):
        tag.setDateAdded(d["dateadded"])
    runtime = d.get("runtime", 0)
    if runtime:
        mins = max(1, runtime // 60)
        li.setProperty("mf.runtime", "%dh %dm" % (mins // 60, mins % 60) if mins >= 60 else "%dm" % mins)
    _extra(tag, d)


def _extra(tag, d):
    """Fields only the details page needs (present when the record came from rpc.details)."""
    if d.get("cast"):
        tag.setCast([xbmc.Actor(c.get("name", ""), c.get("role", ""), c.get("order", 0), c.get("thumbnail", ""))
                     for c in d["cast"]])
    if d.get("director"):
        tag.setDirectors(d["director"])
    if d.get("writer"):
        tag.setWriters(d["writer"])
    if d.get("tag"):
        tag.setTags(d["tag"])
    if d.get("country"):
        tag.setCountries(d["country"])
    if d.get("trailer"):
        tag.setTrailer(d["trailer"])
    if d.get("set"):
        tag.setSet(d["set"])
    if d.get("setid"):
        tag.setSetId(d["setid"])
    if d.get("votes"):
        tag.setVotes(int(d["votes"]) if str(d["votes"]).isdigit() else 0)
    if d.get("uniqueid"):
        tag.setUniqueIDs(d["uniqueid"])


def movie(d):
    li = xbmcgui.ListItem(d.get("title", ""), offscreen=True)
    tag = li.getVideoInfoTag()
    _common(li, tag, d)
    art = dict(d.get("art") or {})
    art["wide"] = art.get("landscape") or art.get("fanart", "")
    li.setArt(art)
    tag.setDbId(d["movieid"])
    tag.setMediaType("movie")
    tag.setYear(d.get("year", 0))
    tag.setDuration(d.get("runtime", 0))
    tag.setMpaa(d.get("mpaa", ""))
    tag.setStudios(d.get("studio") or [])
    tag.setTagLine(d.get("tagline", ""))
    if d.get("premiered"):
        tag.setPremiered(d["premiered"])
    resume = d.get("resume") or {}
    if resume.get("position"):
        tag.setResumePoint(resume["position"], resume.get("total", 0))
    _streams(li, tag, d.get("streamdetails"))
    li.setProperty("mf.left", _left(resume))
    li.setProperty("mf.sub", str(d.get("year") or ""))
    li.setProperty("mf.type", "movie")
    _meta(li, d, "Movie")
    li.setProperty("IsPlayable", "true")
    li.setPath(d.get("file", ""))
    return li, False


def tvshow(d):
    li = xbmcgui.ListItem(d.get("title", ""), offscreen=True)
    tag = li.getVideoInfoTag()
    _common(li, tag, d)
    art = dict(d.get("art") or {})
    art["wide"] = art.get("landscape") or art.get("fanart", "")
    li.setArt(art)
    tag.setDbId(d["tvshowid"])
    tag.setMediaType("tvshow")
    tag.setYear(d.get("year", 0))
    tag.setMpaa(d.get("mpaa", ""))
    tag.setStudios(d.get("studio") or [])
    if d.get("premiered"):
        tag.setPremiered(d["premiered"])
    li.setProperty("TotalEpisodes", str(d.get("episode", 0)))
    li.setProperty("WatchedEpisodes", str(d.get("watchedepisodes", 0)))
    li.setProperty("UnWatchedEpisodes", str(max(0, d.get("episode", 0) - d.get("watchedepisodes", 0))))
    li.setProperty("mf.sub", str(d.get("year") or ""))
    li.setProperty("mf.type", "tvshow")
    _meta(li, d, "Show")
    path = "videodb://tvshows/titles/%d/" % d["tvshowid"]
    li.setPath(path)
    return li, True


def episode(d, show_art=None):
    li = xbmcgui.ListItem(d.get("title", ""), offscreen=True)
    tag = li.getVideoInfoTag()
    _common(li, tag, d)
    art = dict(show_art or {})
    art.update(d.get("art") or {})  # episode thumb wins; show poster/fanart/clearlogo fill the gaps
    for key in ("poster", "fanart", "clearlogo", "landscape"):
        if not art.get(key) and art.get("tvshow." + key):
            art[key] = art["tvshow." + key]
    art["wide"] = art.get("thumb") or art.get("landscape") or art.get("fanart", "")
    li.setArt(art)
    tag.setDbId(d["episodeid"])
    tag.setMediaType("episode")
    tag.setTvShowTitle(d.get("showtitle", ""))
    tag.setSeason(d.get("season", 0))
    tag.setEpisode(d.get("episode", 0))
    tag.setDuration(d.get("runtime", 0))
    if d.get("firstaired"):
        tag.setFirstAired(d["firstaired"])
    resume = d.get("resume") or {}
    if resume.get("position"):
        tag.setResumePoint(resume["position"], resume.get("total", 0))
    _streams(li, tag, d.get("streamdetails"))
    li.setLabel(d.get("showtitle", ""))
    li.setLabel2(d.get("title", ""))
    li.setProperty("mf.left", _left(resume))
    li.setProperty("mf.sub", "S%d · E%d" % (d.get("season", 0), d.get("episode", 0)))
    li.setProperty("mf.type", "episode")
    li.setProperty("IsPlayable", "true")
    li.setPath(d.get("file", ""))
    return li, False


def season(d, tvshowid):
    """A season card: poster, "10 episodes", unwatched count; opens the season's episodes."""
    li = xbmcgui.ListItem(d.get("label") or "Season %d" % d.get("season", 0), offscreen=True)
    art = dict(d.get("art") or {})
    for key in ("poster", "fanart", "clearlogo"):
        if not art.get(key) and art.get("tvshow." + key):
            art[key] = art["tvshow." + key]
    li.setArt(art)
    tag = li.getVideoInfoTag()
    tag.setDbId(d["seasonid"])
    tag.setMediaType("season")
    tag.setSeason(d.get("season", 0))
    tag.setTvShowTitle(d.get("showtitle", ""))
    total, watched = d.get("episode", 0), d.get("watchedepisodes", 0)
    li.setProperty("TotalEpisodes", str(total))
    li.setProperty("WatchedEpisodes", str(watched))
    li.setProperty("UnWatchedEpisodes", str(max(0, total - watched)))
    li.setProperty("mf.sub", "%d episode%s" % (total, "" if total == 1 else "s"))
    li.setProperty("mf.type", "season")
    path = "videodb://tvshows/titles/%d/%d/" % (int(tvshowid), d.get("season", 0))
    li.setPath(path)
    return li, True


def movieset(d):
    """A collection card; opens the collection."""
    li = xbmcgui.ListItem(d.get("title", ""), offscreen=True)
    li.setArt(d.get("art") or {})
    tag = li.getVideoInfoTag()
    tag.setDbId(d["setid"])
    tag.setMediaType("set")
    tag.setPlot(d.get("plot", ""))
    n = len(d.get("movies") or [])
    li.setProperty("mf.sub", "%d movie%s" % (n, "" if n == 1 else "s"))
    li.setProperty("mf.type", "set")
    path = "videodb://movies/sets/%d/" % d["setid"]
    li.setPath(path)
    return li, True


def full(kind, dbid):
    """The details page's item: the whole library record, cast included."""
    from . import rpc
    d = rpc.details(kind, dbid)
    if not d:
        return None
    return {"movie": movie, "tvshow": tvshow, "episode": episode}[kind](d)[0]
