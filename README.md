# MiKiLED for Home Assistant

HACS-compatible custom integration that connects Home Assistant to a [MiKiLED](https://github.com/MiKiLED/MiKiLED) device over its local HTTP API (see the firmware repository `docs/API.md`).

## Features

- **Config flow**: add your device by IP/hostname and port (default 80).
- **Sensors**: temperature, humidity, firmware version, API version, connection mode (`online` / `offline`), current LED period (`day` / `night`), Wi‑Fi RSSI, and uptime (some entities are disabled by default to reduce clutter).
- **Lights**: separate **Day** and **Night** lights mapped to `POST /setDayColor` and `POST /setNightColor` (RGB + brightness; 0–100% on the device).

Polling interval is 30 seconds. The device API is unauthenticated; only expose it on a network you trust.

## Security model

- Traffic is **plain HTTP** to the host you configure (how MiKiLED firmware exposes its API). Use only on a **LAN you trust**; do not expose the device directly to the internet without a reverse proxy and proper access controls.
- Only a **Home Assistant administrator** can add this integration. The configured host is still validated (sane hostname/IP, port range, and **blocking** of the well-known cloud metadata address `169.254.169.254`) to avoid a class of misconfiguration / abuse.
- String values from the device (firmware label, mode, and similar sensors) are **truncated** so a misbehaving peer cannot blow up entity state size.
- If you later add **HTTPS** support in firmware, this integration should be extended to use `https://` with certificate verification enabled by default.

## Install with HACS

1. In HACS, open **Integrations** → **⋮** → **Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Open the **MiKiLED** repository card in HACS, choose version **v1.0.1** (or latest release) if a version menu is shown, then **Download** and restart Home Assistant.
4. Go to **Settings** → **Devices & services** → **Add integration** → **MiKiLED**.

### “Failed to download zipball” in HACS

That message means Home Assistant could not fetch the GitHub archive. Try this order:

1. **Use a release version**: pick **v1.0.1** (or newer) in the HACS version dropdown instead of a branch-only ref, then download again.
2. **GitHub from Home Assistant**: ensure the host can reach `github.com` and `codeload.github.com` (no DNS or firewall blocking). If you use a proxy or ad-blocker on the HA network, allow those hosts.
3. **GitHub API limits**: in HACS → **Settings**, add a [GitHub personal access token](https://github.com/settings/tokens) (classic is fine; scope `public_repo` is enough for public repos) so downloads are less likely to hit anonymous rate limits.
4. **Remove and re-add** the custom repository in HACS, then download again (clears a bad cached ref).

If it still fails, check **Settings → System → Logs** for the full error right after you click Download.

## Manual install

Copy the `custom_components/mikiled` folder into your Home Assistant `config/custom_components/` directory, then restart Home Assistant.

## Publishing this repository

This folder is a standalone Git repository. After `gh auth login`, create and push a public GitHub repository, for example:

```bash
cd home-assistant-mikiled
git remote add origin https://github.com/konkubino/home-assistant-mikiled.git
git push -u origin main
```

Update `documentation` and `issue_tracker` in `custom_components/mikiled/manifest.json` to match your GitHub URL.

## Disclaimer

This project is not affiliated with Home Assistant or Nabu Casa. MiKiLED is an open hardware/firmware project; API behavior follows the firmware version on your device.
