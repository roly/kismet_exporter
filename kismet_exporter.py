#!/usr/bin/env python3

import json
import time
import sys
import os 
from prometheus_client import start_http_server
from prometheus_client.core import CounterMetricFamily,GaugeMetricFamily, REGISTRY
import kismet_rest
from datetime import datetime 


kismet_url = os.getenv('KISMET_URL',None)
kismet_username = os.getenv('KISMET_USERNAME',None)
kismet_password = os.getenv('KISMET_PASSWORD',None)
http_server_port = os.getenv('HTTP_PORT',8501)

devices = kismet_rest.Devices(host_uri=kismet_url,username=kismet_username,password=kismet_password)

class KisCollector(object):

  def __init__(self):
    self.t = int(datetime.utcnow().timestamp())
    self.clientMap = {}
    for device in devices.dot11_access_points():
        bn = device['kismet.device.base.name']
        for client in device['dot11.device']['dot11.device.associated_client_map'].items():
            self.clientMap.setdefault(client[0],set([])).add(bn)


    
  def collect(self):
    
    smetric = GaugeMetricFamily('kismet_device_signal_strength','the signal strength of a device', labels=["mac","ssid","wifi_type","manuf"])
    dmetric = CounterMetricFamily('kismet_device_data_seen','amount of data seen by device', labels=["mac","ssid","wifi_type","manuf"]) 
    pmetric = CounterMetricFamily('kismet_device_packets_seen','number of packets seen',labels=["mac","ssid","wifi_type","manuf"])
    bssmetric = GaugeMetricFamily('kismet_device_bss_timestamp','uptime in seconds of the device',labels=["mac","ssid","wifi_type","manuf"])
    tdmetric =GaugeMetricFamily('kismet_unique_devices','number of devices seen since last query')
    tametric =GaugeMetricFamily('kismet_unique_ap_devices','number of ap devices seen since last query')


    devs = []
    uniq_devices = set() #assuming mac is uniq >;/
    uniq_aps = set() #assuming mac is uniq >;/
    for device in devices.all(ts=self.t):
        ma = device['kismet.device.base.macaddr']
        uniq_devices.add(ma)
        devs.append(device)
        bn = device['kismet.device.base.name']
        if device['kismet.device.base.type'] == 'Wi-Fi AP':
            uniq_aps.add(ma)
            for client in device['dot11.device']['dot11.device.associated_client_map'].items():
                self.clientMap.setdefault(client[0],set([])).add(bn)

    self.t = int(datetime.utcnow().timestamp())

    for device in devs:
        ma = device['kismet.device.base.macaddr']
        ssid = "|".join(self.clientMap.get(ma,set([device['kismet.device.base.commonname']])))
        type = device['kismet.device.base.type']
        manuf = device['kismet.device.base.manuf']
        lastSig = device['kismet.device.base.signal']['kismet.common.signal.last_signal']
        dataSize = device['kismet.device.base.datasize']
        packets = device['kismet.device.base.packets.total']
        if device['dot11.device']['dot11.device.bss_timestamp'] > 0:
            bsstimestamp = device['dot11.device']['dot11.device.bss_timestamp']/1000000
            bssmetric.add_metric([ma,ssid,type,manuf],bsstimestamp)
        smetric.add_metric([ma,ssid,type,manuf], lastSig)
        pmetric.add_metric([ma,ssid,type,manuf], packets)
        dmetric.add_metric([ma,ssid,type,manuf], dataSize)
        
    tametric.add_metric([], len(uniq_aps))
    tdmetric.add_metric([], len(uniq_devices))
    
    yield smetric
    yield dmetric
    yield pmetric
    yield bssmetric
    yield tdmetric
    yield tametric
    

if __name__ == "__main__":
  REGISTRY.register(KisCollector())
  start_http_server(http_server_port)
  while True: time.sleep(1)
