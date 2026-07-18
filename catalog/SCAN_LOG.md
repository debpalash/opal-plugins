# Source-scan coverage log

Honest record of which aggregator pages were actually fetched when building the
`catalog/` files, so coverage gaps are visible rather than assumed.

## Scanned successfully
| Source | Via | Yield |
|---|---|---|
| FMHY `video.md` | GitHub raw | streaming/DDL/torrent/anime firehose (mostly SPA rot, filtered) |
| FMHY `reading.md` | GitHub raw | manga/comics/light-novel/ebook |
| FMHY `audio.md` | GitHub raw | music/audio |
| FMHY `torrenting.md` | GitHub raw | torrent indexers → idope, btdigg, bt4g, torrentquest, torr9, uztracker, rarbgdump |
| awesome-piracy (shakil-shahadat) `Readme.md` | GitHub raw | confirmed the torrent set; libgen/deemix/the-eye |
| everythingmoe.com | WebFetch | ranked anime/manga/torrent → mangago; **flagged AnimeTosho defunct** |
| ~10 user-named torrent sites | `curl` liveness/API probe | domain updates (bitsearch.eu, limetorrents.fun) + new entries |

## Could NOT scan (documented, not silently skipped)
| Source | Reason |
|---|---|
| reddit r/Piracy megathreads (anime / movies_and_tv / music) | The fetcher is **hard-blocked on reddit** (www + old both refused). Not retrievable with available tools. |
| mediasavvy.pages.dev | Landing page only — redirects to `mediasavvy.wiki/Wiki/`; real lists not fetched. |
| hdvinnie Private-Trackers spreadsheet | Excluded by policy (invite-only trackers, not public endpoints) — not fetched. |

## Verified-and-rejected
- **AnimeTosho** (animetosho.org) — everythingmoe ranked it #2, but it **ceased operations 2026-05-09** (frozen, shutting down). Excluded. See torrent-sources.json `excluded`.
- **developify.ca** — 403, purpose unclear; not cataloged pending identification.

## Known remaining gaps (for a future pass)
- The 3 reddit megathreads (need a non-blocked route — e.g. a mirror or manual paste).
- mediasavvy.wiki deep pages.
- FMHY `downloading.md` (DDL) not yet mined beyond `video.md`'s section.
