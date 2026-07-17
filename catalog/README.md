# Source catalog (research staging)

Curated source candidates for [Opal](https://github.com/debpalash/Opal), mined
from public aggregators (FMHY, awesome-piracy, r/Piracy megathreads) plus
user-supplied sites. **These are NOT live plugins.**

## Why a separate catalog instead of the manifest

A `manifest.json` entry only *works* if the app ships a matching engine (the
manifest note: *"torrent ids match the nova2 engine that runs them"*). Adding an
entry for a site with no engine would show a broken, un-installable plugin in the
app. So the split is:

- **`manifest.json`** — engine-backed, actually-installable sources only.
- **`catalog/`** — vetted candidates that still need an engine (or an existing
  engine pointed at a new base). This is the source-of-truth so that engine work
  can proceed one source at a time, each promoted to `manifest.json` when its
  engine lands.

## Files

| File | Contents |
|---|---|
| `torrent-sources.json` | New torrent indexers + a scene release DB, deduped against the manifest's existing torrent plugins. |
| `reading-sources.json` | Manga / comics / light-novel / ebook sources. |
| `anime-sources.json` | API-backed anime sources only; the ad-streaming SPA firehose is deliberately excluded. |

## Entry fields

`engine` — `existing:<id>` if a current app engine fits (often via a base
override), else `needs:<type>` (`html-scrape`, `json-adapter`, `rss`, …).
`reachable` — probe result from a datacenter IP: `confirmed` / `blocked-from-ci`
(refused by geo/UA/Cloudflare — **not** dead) / `unknown`. Verify from a normal
client before committing an engine.

## Deliberately excluded

- **Ad-streaming SPA sites** (hundreds across video/anime/live-TV/sports): rotate
  domains monthly, no stable API, don't fit Opal's torrent+addon+scraper model.
- **Private trackers** (e.g. the hdvinnie spreadsheet): invite-only, not public
  endpoints.

## Prioritization hints

Legal/public-domain sources are the safest first engines: `publicdomaintorrents`,
`comicbookplus`, `royalroad`. `shanaproject` (RSS) and any LibGen **OPDS** mirror
are the cheapest to wire because Opal already has RSS/OPDS handling.
