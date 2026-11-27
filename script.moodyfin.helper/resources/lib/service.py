"""MoodyFin service.

- Window(Home).Property(MoodyFin.Stats)   "1,559 Movies · 241 Shows · 12,212 Episodes"
- Window(Home).Property(MoodyFin.Reload)  changes after playback and library updates; the rows' content paths carry
                                          it, so Kodi fetches them again
- Window(Home).Property(MoodyFin.Ambient) blurred copy of the picture the skin names in its hidden label 9990
                                          (see ambient.py)
"""
import time

import xbmc
import xbmcgui

from . import ambient, rpc

HOME = xbmcgui.Window(10000)
LIBRARY_EVENTS = ("VideoLibrary.OnScanFinished", "VideoLibrary.OnCleanFinished", "VideoLibrary.OnUpdate",
                  "VideoLibrary.OnRemove")
PLAYER_EVENTS = ("Player.OnStop",)


def _stats():
    movies = rpc.count("VideoLibrary.GetMovies", "movies")
    shows = rpc.count("VideoLibrary.GetTVShows", "tvshows")
    episodes = rpc.count("VideoLibrary.GetEpisodes", "episodes")
    parts = []
    for n, word in ((movies, "Movies"), (shows, "Shows"), (episodes, "Episodes")):
        if n:
            parts.append("{:,} {}".format(n, word if n != 1 else word[:-1]))
    HOME.setProperty("MoodyFin.Stats", " · ".join(parts))


class Monitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.dirty_at = 0.0     # when to refresh rows + stats (0 = nothing pending)

    def onNotification(self, sender, method, data):
        if method in LIBRARY_EVENTS or method in PLAYER_EVENTS:
            # many OnUpdate events arrive in a burst during a sync: wait for it to settle
            self.dirty_at = time.time() + (2 if method in PLAYER_EVENTS else 5)


def run():
    monitor = Monitor()
    _stats()
    HOME.setProperty("MoodyFin.Reload", str(int(time.time())))
    amb = ambient.Ambient()
    while not monitor.abortRequested():
        if monitor.dirty_at and time.time() >= monitor.dirty_at and not xbmc.Player().isPlayingVideo():
            monitor.dirty_at = 0.0
            _stats()
            HOME.setProperty("MoodyFin.Reload", str(int(time.time())))
        amb.tick()
        if monitor.waitForAbort(0.25):
            break
    amb.stop()
