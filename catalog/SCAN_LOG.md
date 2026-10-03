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

## Opal connector expansion — 2026-09-29

Implemented and probed through the matching Opal adapters:

- NekoBT: JSON search → magnets (50 sampled anime releases).
- Shana Project: episode search → torrent downloads (50 sampled releases).
- Public Domain Torrents: movie catalog → downloadable torrent metadata.
- Royal Road and NovelFire: search → chapter lists → extracted reading text.
- Weeb Central and ComicBookPlus: listing → chapter/viewer image-page URLs;
  the app served first-page image bytes for both.
- Audius: public tracks and stream URLs; two range probes returned audio bytes.
- Added official NASA, BBC Global News and NPR Up First RSS feed definitions.

ComicBookPlus serves Opal's application User-Agent but rejected the generic
Chrome User-Agent. Its search filters the fetched latest-upload pages. Opal's
current reader caps are 128 comic pages and 400 novel chapters. No torrent media
or full audio file was downloaded during these checks.
One repeated NovelFire chapter request failed transiently; reopening the same
chapter succeeded.

Erai-raws, AcgnX, BT4G and MangaNato probes failed from this network. AnimeParadise
rendered its landing page but its assets were blocked. GetComics and KHInsider
responded; their download chains remain candidates. WuxiaClick needs a valid
search adapter rather than promotion based on a generic listing response.

## Automated reachability scans

Written by `.github/workflows/catalog-reachability.yml`. A probe runs from a datacenter IP, so `blocked-from-ci` and `unknown` mean *we could not see the site*, not that it is gone. Everything above this line is hand-written and is never modified by the workflow.

<!-- BEGIN AUTOMATED-SCANS (managed by .github/workflows/catalog-reachability.yml) -->

### 2026-09-27 12:30 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 36, `error-500`: 1, `unknown`: 3.

| id | file | was | now |
|---|---|---|---|
| `hi10anime` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `lucida` | `stream_rippers` in `music-sources.json` | `blocked-from-ci` | `confirmed` |
| `idope` | `sources` in `torrent-sources.json` | `unknown` | `confirmed` |
| `torrentdownload` | `sources` in `torrent-sources.json` | `confirmed` | `blocked-from-ci` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-09-20 11:53 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 34, `error-500`: 1, `unknown`: 5.

| id | file | was | now |
|---|---|---|---|
| `rapidmoviez` | `release_group_ddl` in `ddl-sources.json` | `error-500` | `confirmed` |
| `hi10anime` | `anime_ddl` in `ddl-sources.json` | `confirmed` | `unknown` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-09-13 12:19 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 34, `error-500`: 2, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `rapidmoviez` | `release_group_ddl` in `ddl-sources.json` | `confirmed` | `error-500` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-09-06 11:23 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 35, `error-500`: 1, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `khinsider` | `legal_api` in `music-sources.json` | `blocked-from-ci` | `confirmed` |
| `nekobt` | `sources` in `torrent-sources.json` | `unknown` | `confirmed` |
| `uztracker` | `sources` in `torrent-sources.json` | `confirmed` | `unknown` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-08-30 12:18 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 26, `confirmed`: 34, `error-500`: 1, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `comicbookplus` | `comics` in `reading-sources.json` | `confirmed` | `blocked-from-ci` |
| `nekobt` | `sources` in `torrent-sources.json` | `confirmed` | `unknown` |
| `uztracker` | `sources` in `torrent-sources.json` | `unknown` | `confirmed` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `uztracker` (torrent-sources.json): https://uztracker.net redirects to https://www.DropCatch.com/domain/uztracker.net (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-08-23 07:22 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 34, `error-500`: 2, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `hi10anime` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `beatrice-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `server-error`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-08-16 07:20 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 34, `error-500`: 1, `unknown`: 5.

| id | file | was | now |
|---|---|---|---|
| `hi10anime` | `anime_ddl` in `ddl-sources.json` | `confirmed` | `unknown` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-08-09 07:42 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 35, `error-500`: 1, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `rapidmoviez` | `release_group_ddl` in `ddl-sources.json` | `blocked-from-ci` | `confirmed` |
| `lucida` | `stream_rippers` in `music-sources.json` | `confirmed` | `blocked-from-ci` |
| `developify` | `sources` in `torrent-sources.json` | `confirmed` | `blocked-from-ci` |
| `torrentdownload` | `sources` in `torrent-sources.json` | `blocked-from-ci` | `confirmed` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `torr9` (torrent-sources.json): https://torr9.net redirects to https://tr4ker.net/ (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

<!-- END AUTOMATED-SCANS -->


## 2026-10-03 — verified content completeness additions

Added three installable definitions, bringing the synchronized catalog to 88:
ComicFury (public creator-hosted full page images), HiAnime (configured exact-episode
ZokoAnime HLS resolution), and Waveform (publisher RSS with complete audio episodes).
Repository research used pinned keiyoushi and ani-cli contracts; implementation is
independent Opal GPL-3.0 code. Real response/media probes and limitations are recorded
in Opal `data/source-research.json` and `docs/browse-sources.md`. A definition remains
inactive until installed, and its existence does not guarantee provider uptime.


## 2026-10-04 — verified public webcomics

Added xkcd and SMBC definitions (90 total), with independent bounded archive/RSS
search and full main-image reader in Opal. xkcd archive+JSON+image and SMBC
RSS+work+image probes succeeded; image transfers were limited to1024bytes.
Original KHInsider albums403, Manganato403, AnimeParadiseAPIunverified, not added.
Detailed pinned GitHub provenance and limits are in Opal data/source-research.json.
