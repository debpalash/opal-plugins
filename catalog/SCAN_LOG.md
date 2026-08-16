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

## Automated reachability scans

Written by `.github/workflows/catalog-reachability.yml`. A probe runs from a datacenter IP, so `blocked-from-ci` and `unknown` mean *we could not see the site*, not that it is gone. Everything above this line is hand-written and is never modified by the workflow.

<!-- BEGIN AUTOMATED-SCANS (managed by .github/workflows/catalog-reachability.yml) -->

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

### 2026-08-02 09:02 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 25, `confirmed`: 35, `error-500`: 1, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `kayoanime` | `anime_ddl` in `ddl-sources.json` | `confirmed` | `blocked-from-ci` |
| `lucida` | `stream_rippers` in `music-sources.json` | `blocked-from-ci` | `confirmed` |
| `getcomics` | `comics` in `reading-sources.json` | `blocked-from-ci` | `confirmed` |
| `developify` | `sources` in `torrent-sources.json` | `blocked-from-ci` | `confirmed` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

### 2026-07-29 14:21 UTC

Probed **65** catalog urls from a GitHub runner. `blocked-from-ci`: 27, `confirmed`: 33, `error-500`: 1, `unknown`: 4.

| id | file | was | now |
|---|---|---|---|
| `animeparadise` | `api_backed` in `anime-sources.json` | `unknown` | `confirmed` |
| `animeonsen` | `api_backed` in `anime-sources.json` | `unknown` | `blocked-from-ci` |
| `miruro` | `api_backed` in `anime-sources.json` | `unknown` | `blocked-from-ci` |
| `seadex` | `metadata_and_quality` in `anime-sources.json` | `unknown` | `confirmed` |
| `tracemoe` | `metadata_and_quality` in `anime-sources.json` | `unknown` | `confirmed` |
| `kitsu` | `metadata_and_quality` in `anime-sources.json` | `unknown` | `confirmed` |
| `kurozora` | `metadata_and_quality` in `anime-sources.json` | `unknown` | `blocked-from-ci` |
| `hdencode` | `release_group_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `rapidmoviez` | `release_group_ddl` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `psarips` | `release_group_ddl` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `nibl` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `kayoanime` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `hi10anime` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `anidl` | `anime_ddl` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `noobsubs` | `anime_ddl` in `ddl-sources.json` | `unknown` | `error-500` |
| `chauthanh` | `anime_ddl` in `ddl-sources.json` | `unknown` | `confirmed` |
| `meawfy` | `warez_scene` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `scnlog` | `warez_scene` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `softarchive` | `warez_scene` in `ddl-sources.json` | `unknown` | `blocked-from-ci` |
| `lrclib` | `legal_api` in `music-sources.json` | `unknown` | `confirmed` |
| `cobalt` | `legal_api` in `music-sources.json` | `unknown` | `confirmed` |
| `bandcamp` | `legal_api` in `music-sources.json` | `unknown` | `blocked-from-ci` |
| `audius` | `legal_api` in `music-sources.json` | `unknown` | `confirmed` |
| `khinsider` | `legal_api` in `music-sources.json` | `unknown` | `blocked-from-ci` |
| `lucida` | `stream_rippers` in `music-sources.json` | `unknown` | `blocked-from-ci` |
| `doubledouble` | `stream_rippers` in `music-sources.json` | `unknown` | `confirmed` |
| `squidwtf` | `stream_rippers` in `music-sources.json` | `unknown` | `confirmed` |
| `deemix` | `stream_rippers` in `music-sources.json` | `unknown` | `confirmed` |
| `mangafire` | `manga` in `reading-sources.json` | `unknown` | `blocked-from-ci` |
| `weebcentral` | `manga` in `reading-sources.json` | `unknown` | `blocked-from-ci` |
| `manganato` | `manga` in `reading-sources.json` | `unknown` | `confirmed` |
| `mangago` | `manga` in `reading-sources.json` | `403-cf` | `blocked-from-ci` |
| `getcomics` | `comics` in `reading-sources.json` | `unknown` | `blocked-from-ci` |
| `comicbookplus` | `comics` in `reading-sources.json` | `unknown` | `confirmed` |
| `royalroad` | `lightnovel` in `reading-sources.json` | `unknown` | `confirmed` |
| `novelfire` | `lightnovel` in `reading-sources.json` | `unknown` | `blocked-from-ci` |
| `wuxiaclick` | `lightnovel` in `reading-sources.json` | `unknown` | `confirmed` |
| `libgen` | `ebook_libraries` in `reading-sources.json` | `unknown` | `confirmed` |
| `kinozal` | `sources` in `torrent-sources.json` | `blocked-from-ci` | `unknown` |
| `publicdomaintorrents` | `sources` in `torrent-sources.json` | `unknown` | `confirmed` |
| `nekobt` | `sources` in `torrent-sources.json` | `error-500` | `confirmed` |
| `idope` | `sources` in `torrent-sources.json` | `blocked-from-ci` | `unknown` |
| `bt4g` | `sources` in `torrent-sources.json` | `403-cf` | `confirmed` |
| `torrentquest` | `sources` in `torrent-sources.json` | `confirmed` | `blocked-from-ci` |
| `uztracker` | `sources` in `torrent-sources.json` | `blocked-from-ci` | `unknown` |
| `rarbgdump` | `sources` in `torrent-sources.json` | `confirmed` | `blocked-from-ci` |
| `developify` | `sources` in `torrent-sources.json` | `403-cf` | `blocked-from-ci` |
| `rustorka` | `sources` in `torrent-sources.json` | `unknown` | `blocked-from-ci` |
| `torrentdownload` | `sources` in `torrent-sources.json` | `unknown` | `blocked-from-ci` |
| `xrel` | `release_db` in `torrent-sources.json` | `unknown` | `confirmed` |

Notes:

- `royalroad` (reading-sources.json): https://www.royalroad.com redirects to https://www.royalroad.com/home (catalog url left as-is; confirm before editing)
- `rutracker` (torrent-sources.json): https://rutracker.org redirects to https://rutracker.org/forum/index.php (catalog url left as-is; confirm before editing)
- `erai-raws` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`
- `acgnx` (torrent-sources.json): kept `community` (community-vouched); CI saw `blocked`

<!-- END AUTOMATED-SCANS -->
