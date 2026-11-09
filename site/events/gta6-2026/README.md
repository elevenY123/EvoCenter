# GTA VI limited visual edition

The event is active from **2026-11-10 00:00 Asia/Shanghai** until, but not including,
**2026-11-20 00:00 Asia/Shanghai**. The same absolute interval is used worldwide.

- Website: `site/event-theme.js` gates the CSS, hero, icons and browser banners.
- Store: `Tools/event-theme.py` reconciles Sileo icons, native depiction headers,
  featured banners and APT checksums. `.github/workflows/event-theme.yml` runs at
  both boundaries with retries, as well as on a daily reconciliation schedule.
  The event workflow disables itself after the final successful restoration.
- The workflow explicitly requests a Pages build after the bot push. It does not
  rely on a bot commit triggering a second workflow.
- Original image files stay untouched. `normal.json` retains normal metadata and
  image hashes. Restore only replaces fields that still contain this event's URL
  or tint; unrelated package updates and content edits are preserved.
- No DEB, package version, runtime code, installed settings icon, or screenshot is
  changed for this store-only visual event.

Commands:

```sh
python Tools/check-event-theme.py
python Tools/event-theme.py                  # reconcile against current time
python Tools/event-theme.py --at 2026-11-20T00:00:00+08:00  # restore store artwork
```

Use `?preview=gta6` on a browser page for an explicit visual preview. Normal
visitors get the standard design before and after the event. Existing open pages
also recheck their state at each time boundary and on returning to the tab.

Assets were made with built-in image_gen from the approved plugin artwork,
inspired by [GTA VI's official site](https://www.rockstargames.com/VI) and
[promotional media](https://www.rockstargames.com/VI/media). Web exports are resized
from separate master images; the source artwork is not a game screenshot.
