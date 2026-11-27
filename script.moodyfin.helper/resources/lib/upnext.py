"""Up Next: 30 s before a library episode ends, a pop-up offers the next one, and plays it when this one ends.

The pop-up is the skin's MoodyFin-UpNext.xml (a WindowXMLDialog): 3001 Play now, 3002 Cancel.
Its labels are window properties: mf.title, mf.sub ("S1 · E4 · Title"), mf.thumb, mf.left ("Starting in 12 s").
Stays out of the way when the Up Next add-on (service.upnext) is installed, or the skin setting mf.noupnext is on.
"""
import threading

import xbmc
import xbmcaddon
import xbmcgui

from . import rpc

LEAD = 30  # seconds before the end


def _next_episode(epid):
    cur = rpc.call("VideoLibrary.GetEpisodeDetails",
                   {"episodeid": epid, "properties": ["tvshowid", "season", "episode"]}).get("episodedetails")
    if not cur:
        return None
    eps = rpc.episodes({"method": "episode", "order": "ascending"}, 10000, tvshowid=cur["tvshowid"])
    key = (cur["season"], cur["episode"])
    later = [e for e in eps if e.get("season", 0) > 0 and (e.get("season"), e.get("episode")) > key]
    return later[0] if later else None


class Dialog(xbmcgui.WindowXMLDialog):
    def onInit(self):
        self.choice = None
        try:
            self.setFocusId(3001)
        except RuntimeError:
            pass

    def onClick(self, control_id):
        self.choice = "play" if control_id == 3001 else "cancel"
        self.close()

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_PREVIOUS_MENU):
            self.choice = "cancel"
            self.close()


class UpNext(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.next = None        # the next episode's record
        self.shown = False
        self.cancelled = False
        self.dialog = None

    # -- player events
    def onAVStarted(self):
        self.reset()
        try:
            tag = self.getVideoInfoTag()
            if tag.getMediaType() == "episode" and tag.getDbId() > 0:
                self.next = _next_episode(tag.getDbId())
        except RuntimeError:
            pass

    def onPlayBackStopped(self):
        self._close()
        self.reset()

    def onPlayBackEnded(self):
        nxt, cancelled = self.next, self.cancelled
        self._close()
        self.reset()
        if nxt and not cancelled:
            rpc.call("Player.Open", {"item": {"episodeid": nxt["episodeid"]}})

    # -- called by the service loop
    def tick(self):
        if not self.next or self.cancelled or not self.isPlayingVideo():
            return
        if xbmc.getCondVisibility("System.HasAddon(service.upnext) | Skin.HasSetting(mf.noupnext)"):
            return
        try:
            left = self.getTotalTime() - self.getTime()
        except RuntimeError:
            return
        if self.dialog is not None:
            self.dialog.setProperty("mf.left", "Starting in %d s" % max(0, int(left)))
        if not self.shown and 0 < left <= LEAD:
            self.shown = True
            threading.Thread(target=self._show, daemon=True).start()

    def _show(self):
        e = self.next
        art = e.get("art") or {}
        path = xbmcaddon.Addon().getAddonInfo("path")
        self.dialog = Dialog("MoodyFin-UpNext.xml", path, "default", "1080i")
        self.dialog.setProperty("mf.title", e.get("showtitle", ""))
        self.dialog.setProperty("mf.sub", "S%d · E%d · %s" % (e.get("season", 0), e.get("episode", 0), e.get("title", "")))
        self.dialog.setProperty("mf.thumb", art.get("thumb") or art.get("tvshow.fanart", ""))
        self.dialog.setProperty("mf.left", "")
        self.dialog.doModal()
        choice = getattr(self.dialog, "choice", None)
        self.dialog = None
        if choice == "play" and self.next:
            nxt, self.next = self.next, None
            rpc.call("Player.Open", {"item": {"episodeid": nxt["episodeid"]}})
        elif choice == "cancel":
            self.cancelled = True

    def _close(self):
        if self.dialog is not None:
            try:
                self.dialog.close()
            except RuntimeError:
                pass


def preview(epid):
    """Show the pop-up for an episode without playing anything (testing / the skin's preview)."""
    up = UpNext()
    up.next = _next_episode(int(epid)) or rpc.call(
        "VideoLibrary.GetEpisodeDetails",
        {"episodeid": int(epid), "properties": rpc.EPISODE_PROPS}).get("episodedetails")
    if up.next and "art" not in up.next:
        up.next = rpc.call("VideoLibrary.GetEpisodeDetails",
                           {"episodeid": up.next["episodeid"], "properties": rpc.EPISODE_PROPS}).get("episodedetails")
    if up.next:
        up._show()
