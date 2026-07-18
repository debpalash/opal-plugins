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

## Scanned via user-pasted content (fetcher is hard-blocked on reddit)
The fetcher cannot reach reddit (www + old both refused), so these were provided
as pasted wiki JSON and scanned from that:
| Page | Yield |
|---|---|
| r/Piracy megathread **anime** | SubsPlease, Erai-raws, Beatrice-Raws, Drevos, Project AcgnX (torrents); NoobSubs, ChauThanh (DDL); SeaDex, trace.moe, Kitsu, Kurozora (metadata/quality APIs) |
| r/Piracy megathread **all-purpose** | Rustorka, TorrentDownload.info, **developify (resolved)** (torrents); Meawfy, Scnlog, SoftArchive (warez/scene); xREL (scene DB) |

## Could NOT scan (still open)
| Source | Reason |
|---|---|
| reddit megathreads **movies_and_tv** + **music** | Same reddit block — paste them and I'll fold them in. |
| mediasavvy.pages.dev | Landing page only — redirects to `mediasavvy.wiki/Wiki/`; real lists not fetched. |
| hdvinnie Private-Trackers spreadsheet | Excluded by policy (invite-only trackers, not public endpoints). |

## Verified / resolved
- **developify.ca** — earlier "purpose unclear (403)"; the all-purpose megathread identifies it as **"The Torrent Database"**. Promoted from `excluded` to a real torrent source.
- **AnimeTosho** (animetosho.org) — CONFLICT: the site showed a "ceased operations 2026-05-09" notice when probed, but the anime megathread (moderator-approved, ~Jul 2026) still lists it active. Left in `excluded` with the conflict noted — verify before wiring.

## Known remaining gaps (for a future pass)
- The 3 reddit megathreads (need a non-blocked route — e.g. a mirror or manual paste).
- mediasavvy.wiki deep pages.
- FMHY `downloading.md` (DDL) not yet mined beyond `video.md`'s section.
