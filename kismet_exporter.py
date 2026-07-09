#!/usr/bin/env python3

import time
import os
from datetime import datetime, timezone
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
import kismet_rest
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
            if lastSig is not None:
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


if __name__ == "__main__":
    REGISTRY.register(KisCollector())
    start_http_server(http_server_port)
    while True:
        time.sleep(60)
