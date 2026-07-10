#!/usr/bin/env python3

import time
import os
from datetime import datetime, timezone
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
import kismet_rest
import requests
from pd_lookup import search as pdsearch

kismet_url = os.getenv('KISMET_URL', None)
kismet_username = os.getenv('KISMET_USERNAME', None)
kismet_password = os.getenv('KISMET_PASSWORD', None)
http_server_port = int(os.getenv('HTTP_PORT', 8501))

devices = kismet_rest.Devices(host_uri=kismet_url, username=kismet_username, password=kismet_password)
PDlookup = pdsearch.PersonalDevice()

LABELS = ["mac", "ssid", "wifi_type", "manuf", "personal_device", "personal_device_match"]

# kismet_rest's Devices.all() doesn't support Kismet's field-simplification
# filter, so it always returns the full device object (signal RRDs, packet
# histograms, seenby maps, dot11 client lists, tags, ...) instead of just the
# handful of scalar fields below. On a busy Kismet instance that's tens of KB
# per device instead of a few hundred bytes, which is where scrape latency
# was actually going. Request only what's used, via devices.interact_yield()
# directly (bypassing .all()) with Kismet's field simplification/rename syntax.
DEVICE_FIELDS = [
    "kismet.device.base.macaddr",
    "kismet.device.base.commonname",
    "kismet.device.base.type",
    "kismet.device.base.manuf",
    "kismet.device.base.frequency",
    "kismet.device.base.datasize",
    "kismet.device.base.packets.total",
    ["kismet.device.base.signal/kismet.common.signal.last_signal", "kismet.device.base.signal.last_signal"],
    ["dot11.device/dot11.device.bss_timestamp", "dot11.device.bss_timestamp"],
]

# Data-source health. Kismet's /datasource/all_sources.json is polled at most
# every SOURCE_CACHE_TTL seconds and cached, so it doesn't add a Kismet
# round-trip to every Prometheus scrape (which has a 1.5s timeout).
SOURCE_CACHE_TTL = 8
_source_cache = {"ts": 0.0, "data": []}

def get_sources():
    now = time.time()
    if _source_cache["data"] and now - _source_cache["ts"] < SOURCE_CACHE_TTL:
        return _source_cache["data"]
    try:
        resp = requests.get(
            "{}/datasource/all_sources.json".format(kismet_url),
            auth=(kismet_username, kismet_password), timeout=1.0)
        resp.raise_for_status()
        _source_cache["data"] = resp.json()
        _source_cache["ts"] = now
    except Exception:
        pass  # keep last-known data on a transient failure
    return _source_cache["data"]


class KisCollector(object):

    def __init__(self):
        self.t = int(datetime.now(timezone.utc).timestamp())

    def collect(self):
        smetric = GaugeMetricFamily('kismet_device_signal_strength', 'the signal strength of a device', labels=LABELS)
        dmetric = CounterMetricFamily('kismet_device_data_seen', 'amount of data seen by device', labels=LABELS)
        pmetric = CounterMetricFamily('kismet_device_packets_seen', 'number of packets seen', labels=LABELS)
        bssmetric = GaugeMetricFamily('kismet_device_bss_timestamp', 'uptime in seconds of the device', labels=LABELS)
        fmetric = GaugeMetricFamily('kismet_device_freq', 'freq of the device', labels=LABELS)

        PDlookup.reload_if_changed()

        last = self.t
        self.t = int(datetime.now(timezone.utc).timestamp())

        url = "devices/last-time/{}/devices.itjson".format(last)
        for device in devices.interact_yield("POST", url, payload={"fields": DEVICE_FIELDS}):
            ma = device['kismet.device.base.macaddr']
            ssid = device['kismet.device.base.commonname']
            dev_type = device['kismet.device.base.type']
            manuf = device['kismet.device.base.manuf']
            pd, pdm = PDlookup.search(ssid, manuf)
            label_values = [ma, ssid, dev_type, manuf, pd, pdm]

            fmetric.add_metric(label_values, device['kismet.device.base.frequency'])

            lastSig = device.get('kismet.device.base.signal.last_signal')
            # Kismet reports last_signal = 0 dBm when it has no valid RSSI for a
            # device (common for ad-hoc/AWDL peer devices). Real signal is always
            # negative, so skip the 0 placeholder — otherwise the signal_index
            # rule turns it into 2*(0+100)=200, painting a max-strength lane for
            # a device we can't actually hear.
            if lastSig is not None and lastSig < 0:
                smetric.add_metric(label_values, lastSig)

            dmetric.add_metric(label_values, device['kismet.device.base.datasize'])
            pmetric.add_metric(label_values, device['kismet.device.base.packets.total'])

            bsstimestamp = device.get('dot11.device.bss_timestamp') or 0
            if bsstimestamp > 0:
                bssmetric.add_metric(label_values, bsstimestamp / 1000000)

        yield smetric
        yield dmetric
        yield pmetric
        yield bssmetric
        yield fmetric

        # Data-source health, so the kiosk can show "N/M radios live" and catch a
        # stalled source (running but its packet counter has stopped growing).
        runmetric = GaugeMetricFamily('kismet_datasource_running',
                                      'kismet data source running (1) or not (0)',
                                      labels=['source', 'interface'])
        srcpktmetric = CounterMetricFamily('kismet_datasource_packets',
                                           'total packets captured by a data source',
                                           labels=['source', 'interface'])
        for s in get_sources():
            name = str(s.get('kismet.datasource.name', ''))
            iface = s.get('kismet.datasource.interface', '') or ''
            running = 1.0 if s.get('kismet.datasource.running') else 0.0
            pkts = s.get('kismet.datasource.num_packets') or 0
            runmetric.add_metric([name, iface], running)
            srcpktmetric.add_metric([name, iface], float(pkts))
        yield runmetric
        yield srcpktmetric


if __name__ == "__main__":
    REGISTRY.register(KisCollector())
    start_http_server(http_server_port)
    while True:
        time.sleep(60)
