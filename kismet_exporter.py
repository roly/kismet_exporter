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

        for device in devices.all(ts=last):
            ma = device['kismet.device.base.macaddr']
            ssid = device['kismet.device.base.commonname']
            dev_type = device['kismet.device.base.type']
            manuf = device['kismet.device.base.manuf']
            pd, pdm = PDlookup.search(ssid, manuf)
            label_values = [ma, ssid, dev_type, manuf, pd, pdm]

            fmetric.add_metric(label_values, device['kismet.device.base.frequency'])

            if 'kismet.device.base.signal' in device:
                lastSig = device['kismet.device.base.signal']['kismet.common.signal.last_signal']
                smetric.add_metric(label_values, lastSig)

            dmetric.add_metric(label_values, device['kismet.device.base.datasize'])
            pmetric.add_metric(label_values, device['kismet.device.base.packets.total'])

            if 'dot11.device' in device and device['dot11.device']['dot11.device.bss_timestamp'] > 0:
                bsstimestamp = device['dot11.device']['dot11.device.bss_timestamp'] / 1000000
                bssmetric.add_metric(label_values, bsstimestamp)

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
