# Opal Plugins

Source **endpoints and credentials** for [Opal](https://github.com/debpalash/Opal).

Opal ships with the connector *code* but **no live source URLs**. Each entry in
`manifest.json` supplies the URL/API/keys for one source. Opal's in-app **Plugins**
manager installs a selected source into `~/.config/zigzag/plugins/sources/<id>.json`;
until then that source is inert.

## Trust & responsibility
Installing a source connects Opal to a third-party service you choose. Their content
and its legality vary by region and are **your responsibility** — see Opal's
[CONTENT_POLICY](https://github.com/debpalash/Opal/blob/main/CONTENT_POLICY.md).
These entries are endpoints only; no media is hosted here.

## Format
`manifest.json` → `plugins[]`: `{ id, name, type, version, endpoints{}, [headers{}], [key] }`.
