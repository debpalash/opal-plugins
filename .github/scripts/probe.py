#!/usr/bin/env python3
"""Shared HTTP probe helper for the opal-plugins maintenance workflows.

Stdlib only. Networking is delegated to `curl` (already present on GitHub's
runners) because it handles the TLS/HTTP2/redirect edge cases that these
often-hostile endpoints throw far better than urllib does.

The single rule that governs everything here: a probe run from a datacenter IP
cannot distinguish "this site is dead" from "this site refuses datacenter IPs".
So we never emit a verdict that means "dead". The worst verdict we emit is
"unreachable-from-ci", which is a statement about our vantage point, not about
the site.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

# A real, honest User-Agent. Identifies the bot and points at the repo so an
# operator who sees it in their logs knows who to contact.
USER_AGENT = (
    "Mozilla/5.0 (compatible; opal-plugins-linkcheck/1.0; "
    "+https://github.com/debpalash/opal-plugins)"
)

# Be polite: a small pool, not a flood. These are mostly small volunteer-run
# sites and we touch each host at most twice per run.
DEFAULT_CONCURRENCY = 6
DEFAULT_TIMEOUT = 20
DEFAULT_CONNECT_TIMEOUT = 10

# Verdicts. Deliberately closed vocabulary -- see module docstring.
OK = "ok"                              # 2xx
REDIRECT = "redirect"                  # ended somewhere else, still 2xx
REDIRECT_LOOP = "redirect-loop"        # still 3xx after following the chain
BLOCKED = "blocked"                    # 401/403/429/CF challenge -- our IP, not the site
SERVER_ERROR = "server-error"          # 5xx
NOT_FOUND = "not-found"                # 404/410
UNREACHABLE = "unreachable-from-ci"    # DNS / connect / TLS / timeout
SKIPPED = "skipped"                    # not probeable (template, loopback, ...)

# Verdicts that are safe to describe as "the endpoint is fine".
HEALTHY = {OK, REDIRECT}

# curl exit codes worth distinguishing in the report.
_CURL_EXIT = {
    6: "dns-resolve-failed",
    7: "connection-refused",
    28: "timeout",
    35: "tls-handshake-failed",
    56: "connection-reset",
    60: "tls-cert-invalid",
}

_TEMPLATE_RE = re.compile(r"[{}]")
_LOOPBACK_RE = re.compile(
    r"^https?://(127\.0\.0\.1|localhost|0\.0\.0\.0|\[::1\])(:|/|$)", re.I
)


@dataclass
class ProbeResult:
    url: str
    verdict: str
    status: int = 0
    final_url: str = ""
    # Status of the FIRST hop only, before any redirect was followed. This is
    # what tells us whether a move is permanent (301/308) or transient (302/307).
    first_status: int = 0
    redirect_url: str = ""
    detail: str = ""
    body_head: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return self.verdict in HEALTHY

    @property
    def moved(self) -> bool:
        return bool(self.final_url) and self.final_url.rstrip("/") != self.url.rstrip("/")

    def as_dict(self) -> dict:
        return {
            "url": self.url,
            "verdict": self.verdict,
            "status": self.status,
            "first_status": self.first_status,
            "final_url": self.final_url,
            "redirect_url": self.redirect_url,
            "detail": self.detail,
        }


def is_probeable(url) -> bool:
    """False for anything a link check cannot meaningfully resolve."""
    if not isinstance(url, str):
        return False
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return False
    if _TEMPLATE_RE.search(url):
        return False          # "{provider}={key}" style templates
    if _LOOPBACK_RE.match(url):
        return False          # e.g. jackett's http://127.0.0.1:9117
    return True


def extract_url(raw):
    """Pull the first URL out of a field that may carry prose.

    Some catalog entries read like "https://predb.net (alt: https://predb.me)".
    """
    if not isinstance(raw, str):
        return None
    m = re.search(r"https?://[^\s,;)\]\"']+", raw)
    return m.group(0) if m else None


def _looks_like_cloudflare(status: int, headers: str, body: str) -> bool:
    h = headers.lower()
    b = body.lower()
    if "cf-mitigated" in h or "cf-chl" in h:
        return True
    if status in (403, 503) and ("cloudflare" in h or "cloudflare" in b):
        return True
    if "just a moment" in b or "attention required" in b or "error 1020" in b:
        return True
    if "ddos-guard" in h or "ddos-guard" in b:
        return True
    return False


def probe(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    method: str = "GET",
) -> ProbeResult:
    """Probe one URL. Never raises; every failure becomes a verdict."""
    if not is_probeable(url):
        return ProbeResult(url=url, verdict=SKIPPED, detail="not a probeable URL")

    # Two curl calls:
    #   1. no -L, to capture the FIRST hop verbatim (301 vs 302 matters a lot).
    #   2. -L, to see where the chain actually lands.
    base = [
        "curl", "-sS", "-A", USER_AGENT,
        "--connect-timeout", str(connect_timeout),
        "--max-time", str(timeout),
        "--max-redirs", "5",
        "--max-filesize", "5000000",   # best-effort; we only need the head of the body
        "--compressed",
        "-H", "Accept: */*",
        "-H", "Accept-Language: en-US,en;q=0.9",
    ]
    if method == "HEAD":
        base += ["-I"]

    first_status = 0
    redirect_url = ""
    try:
        p1 = subprocess.run(
            base + ["-o", "/dev/null", "-D", "-",
                    "-w", "\n__STATUS__%{http_code}\n__REDIR__%{redirect_url}\n", url],
            capture_output=True, timeout=timeout + connect_timeout + 15,
        )
        # Bytes, not text=True: these endpoints serve latin-1, shift-jis and
        # outright binary, and a decode error must never abort a link check.
        out1 = (p1.stdout or b"").decode("utf-8", "replace")
        m = re.search(r"__STATUS__(\d+)", out1)
        if m:
            first_status = int(m.group(1))
        m = re.search(r"__REDIR__(\S*)", out1)
        if m:
            redirect_url = m.group(1)
    except subprocess.TimeoutExpired:
        return ProbeResult(url=url, verdict=UNREACHABLE, detail="timeout (first hop)")
    except OSError as exc:
        return ProbeResult(url=url, verdict=UNREACHABLE, detail=f"curl failed: {exc}")

    # Second call follows the chain and grabs a little body for CF detection.
    try:
        p2 = subprocess.run(
            base + ["-L", "-D", "-", "-o", "-",
                    "-w", "\n__STATUS__%{http_code}\n__FINAL__%{url_effective}\n", url],
            capture_output=True, timeout=(timeout * 2) + connect_timeout + 20,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(url=url, verdict=UNREACHABLE, status=first_status,
                           first_status=first_status, redirect_url=redirect_url,
                           detail="timeout")
    except OSError as exc:
        return ProbeResult(url=url, verdict=UNREACHABLE, detail=f"curl failed: {exc}")

    out = (p2.stdout or b"").decode("utf-8", "replace")
    status = 0
    final_url = ""
    m = re.search(r"__STATUS__(\d+)", out)
    if m:
        status = int(m.group(1))
    m = re.search(r"__FINAL__(\S*)", out)
    if m:
        final_url = m.group(1)

    if p2.returncode != 0 and status == 0:
        detail = _CURL_EXIT.get(p2.returncode, f"curl exit {p2.returncode}")
        err = (p2.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        if err:
            detail = f"{detail}: {err[-1][:160]}"
        return ProbeResult(url=url, verdict=UNREACHABLE, first_status=first_status,
                           redirect_url=redirect_url, detail=detail,
                           meta={"curl_exit": p2.returncode})

    body_head = out[:4000]
    headers = "\n".join(l for l in out.splitlines() if ":" in l[:40])[:4000]

    if _looks_like_cloudflare(status, headers, body_head):
        verdict = BLOCKED
        detail = "challenge/WAF interstitial"
    elif 200 <= status < 300:
        verdict = REDIRECT if (final_url and final_url.rstrip("/") != url.rstrip("/")) else OK
        detail = ""
    elif status in (401, 403, 429):
        verdict = BLOCKED
        detail = f"HTTP {status}"
    elif status in (404, 410):
        verdict = NOT_FOUND
        detail = f"HTTP {status}"
    elif 300 <= status < 400:
        # Still redirecting after -L exhausted --max-redirs. Usually an
        # https->http->https ping-pong (torrentfunk2 does exactly this).
        verdict = REDIRECT_LOOP
        detail = f"HTTP {status} after following redirects (loop or too many hops)"
    elif 500 <= status < 600:
        verdict = SERVER_ERROR
        detail = f"HTTP {status}"
    elif status == 0:
        verdict = UNREACHABLE
        detail = "no response"
    else:
        verdict = BLOCKED
        detail = f"HTTP {status}"

    return ProbeResult(
        url=url, verdict=verdict, status=status, final_url=final_url,
        first_status=first_status, redirect_url=redirect_url, detail=detail,
        body_head=body_head,
    )


def probe_many(urls, concurrency: int = DEFAULT_CONCURRENCY, **kw) -> dict:
    """Probe a de-duplicated iterable of URLs. Returns {url: ProbeResult}."""
    uniq = list(dict.fromkeys(urls))
    if not uniq:
        return {}
    if shutil.which("curl") is None:
        raise SystemExit("FATAL: curl not found on PATH")
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        results = list(pool.map(lambda u: probe(u, **kw), uniq))
    return dict(zip(uniq, results))


def fetch_json(url: str, timeout: int = 180, expect_min_bytes: int = 64,
               return_raw: bool = False):
    """Download a URL and parse it as JSON, or raise RuntimeError.

    Used for the `lists/` mirror, where committing a truncated download or an
    HTML error page over good data is the failure mode we care most about.

    With return_raw=True, yields (parsed, original_bytes) so the caller can
    store upstream's bytes verbatim. That matters here: these files are
    minified and served raw to users, and re-serialising them would inflate
    manga-full.json from ~12 MB to ~30 MB for no benefit, as well as making
    every diff unreadable.
    """
    cmd = [
        "curl", "-sS", "-L", "-A", USER_AGENT,
        "--connect-timeout", "15",
        "--max-time", str(timeout),
        "--retry", "3", "--retry-delay", "5", "--retry-connrefused",
        "--fail-with-body",
        "--compressed",
        "-w", "\n__STATUS__%{http_code}",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{url}: download timed out after {timeout}s")

    raw = proc.stdout or b""
    marker = raw.rfind(b"\n__STATUS__")
    if marker == -1:
        stderr = (proc.stderr or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(f"{url}: curl produced no status marker ({stderr[:200]})")
    status = int(raw[marker + len(b"\n__STATUS__"):].strip() or 0)
    body = raw[:marker]

    if status != 200:
        raise RuntimeError(f"{url}: HTTP {status} (expected 200)")
    if len(body) < expect_min_bytes:
        raise RuntimeError(f"{url}: response only {len(body)} bytes -- refusing to trust it")

    head = body.lstrip()[:1].decode("utf-8", "replace")
    if head not in "[{":
        snippet = body.lstrip()[:120].decode("utf-8", "replace")
        raise RuntimeError(f"{url}: body is not JSON (starts with {snippet!r})")

    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{url}: payload did not parse as JSON: {exc}")

    return (parsed, body) if return_raw else parsed
