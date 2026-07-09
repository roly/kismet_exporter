# kismet_exporter

A Prometheus exporter that polls the [Kismet](https://www.kismetwireless.net/) wireless network detector REST API and classifies nearby WiFi devices for use in Grafana dashboards and alerting.

## What it does

- Queries Kismet incrementally (only devices updated since the last scrape) via `kismet_rest`
- Classifies each device as `car`, `cam`, `hotspot`, or `other` by matching its SSID and manufacturer against regex pattern files
- Exposes metrics on port 8501 for Prometheus to scrape

## Metrics

| Metric | Type | Description |
|---|---|---|
| `kismet_device_signal_strength` | Gauge | Last signal strength (dBm) |
| `kismet_device_data_seen` | Counter | Total bytes seen |
| `kismet_device_packets_seen` | Counter | Total packets seen |
| `kismet_device_bss_timestamp` | Gauge | Device uptime in seconds |
| `kismet_device_freq` | Gauge | Operating frequency |

All metrics share labels: `mac`, `ssid`, `wifi_type`, `manuf`, `personal_device`, `personal_device_match`.

## Project layout

```
kismet_exporter.py      # Main exporter — custom Prometheus collector
pd_lookup/
  search.py             # PersonalDevice class — pattern loading and matching
  txt/                  # Pattern files, one device type per file
    01_car              # Vehicle SSIDs/manufacturers
    02_cam              # Dashcam SSIDs/manufacturers
    03_hotspot          # Mobile hotspot patterns
    04_other            # Miscellaneous personal devices
  test.py               # Unit tests for search logic
requirements.txt        # Python dependencies
Dockerfile              # python:3.12-slim image
docker-compose.yml      # Mounts pd_lookup/txt as a volume for live reloading
```

## Running locally

```bash
pip install -r requirements.txt
export KISMET_URL=http://your-kismet-host:2501
export KISMET_USERNAME=youruser
export KISMET_PASSWORD=yourpassword
python kismet_exporter.py
# metrics available at http://localhost:8501/metrics
```

## Docker

```bash
cp kismet_exporter.env.example kismet_exporter.env
# edit kismet_exporter.env with your Kismet credentials
docker-compose up -d
```

The `pd_lookup/txt/` directory is volume-mounted into the container. Edit pattern files on the host and the next Prometheus scrape (typically 15–60s) will automatically pick up the changes — no restart needed.

## Adding or editing patterns

Pattern files in `pd_lookup/txt/` are named `<priority>_<type>` (e.g. `01_car`, `02_cam`). Lower number = higher match priority. Each line is a Python regex (case-insensitive). To add a new device type, create a new numbered file following the same convention.

The `PersonalDevice` class pre-compiles all regexes at startup and caches results per input string. `reload_if_changed()` is called on every scrape; if any file's mtime has changed the cache is cleared and patterns are reloaded.

## Tests

```bash
python test.py
python pd_lookup/test.py
```

## Key design decisions

- **Incremental polling**: `devices.all(ts=last)` fetches only devices updated since the previous scrape, keeping the Kismet API load low.
- **Pre-compiled regexes**: All ~212 patterns are compiled once at startup, not on every match attempt. This was the primary CPU bottleneck.
- **In-memory cache**: Each unique SSID/manufacturer string is cached after its first match so repeat devices cost nothing.
- **Volume-mounted patterns**: `pd_lookup/txt/` is not baked into the Docker image at runtime; it lives on the host for easy editing.
