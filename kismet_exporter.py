#!/usr/bin/env python3

import json
import time
import sys
import os 
from prometheus_client import start_http_server
from prometheus_client.core import CounterMetricFamily,GaugeMetricFamily, REGISTRY
import kismet_rest
from datetime import datetime 
from pd_lookup import search as pdsearch

kismet_url = os.getenv('KISMET_URL',None)
kismet_username = os.getenv('KISMET_USERNAME',None)
kismet_password = os.getenv('KISMET_PASSWORD',None)
http_server_port = os.getenv('HTTP_PORT',8501)

devices = kismet_rest.Devices(host_uri=kismet_url,username=kismet_username,password=kismet_password)
PDlookup = pdsearch.PersonalDevice()

class KisCollector(object):

  def __init__(self):
    self.t = int(datetime.utcnow().timestamp())
    #self.clientMap = {}
    #for device in devices.dot11_access_points():
    #    bn = device['kismet.device.base.name']
    #    try: 

    #       if device['dot11.device']['dot11.device.num_associated_clients'] > 0:
    #            for client in device['dot11.device']['dot11.device.associated_client_map'].items():
    #                self.clientMap.setdefault(client[0],set([])).add(bn)
    #    except: 
    #        pass

    
  def collect(self):
    
    smetric = GaugeMetricFamily('kismet_device_signal_strength','the signal strength of a device', labels=["mac","ssid","wifi_type","manuf","personal_device","personal_device_match"])
    dmetric = CounterMetricFamily('kismet_device_data_seen','amount of data seen by device', labels=["mac","ssid","wifi_type","manuf","personal_device","personal_device_match"]) 
    pmetric = CounterMetricFamily('kismet_device_packets_seen','number of packets seen',labels=["mac","ssid","wifi_type","manuf","personal_device","personal_device_match"])
    bssmetric = GaugeMetricFamily('kismet_device_bss_timestamp','uptime in seconds of the device',labels=["mac","ssid","wifi_type","manuf","personal_device","personal_device_match"])
    fmetric = GaugeMetricFamily('kismet_device_freq','freq of the device',labels=["mac","ssid","wifi_type","manuf","personal_device","personal_device_match"])


    devs = []
    last = self.t
    self.t = int(datetime.utcnow().timestamp())
    for device in devices.all(ts=last):
        ma = device['kismet.device.base.macaddr']
        devs.append(device)
        bn = device['kismet.device.base.name']
        #if device['kismet.device.base.type'] == 'Wi-Fi AP':
        #    try: 
        #        if device['dot11.device']['dot11.device.num_associated_clients'] > 0:
        #            for client in device['dot11.device']['dot11.device.associated_client_map'].items():
        #                self.clientMap.setdefault(client[0],set([])).add(bn)
        #    except: 
        #        pass

    for device in devs:
        ma = device['kismet.device.base.macaddr']
        #ssid = "|".join(self.clientMap.get(ma,set([device['kismet.device.base.commonname']])))
        ssid = device['kismet.device.base.commonname']
        type = device['kismet.device.base.type']
        manuf = device['kismet.device.base.manuf']
#        pd,pdm = ["",""]`
        pd,pdm = PDlookup.search(ssid,manuf)
        fmetric.add_metric([ma,ssid,type,manuf,pd,pdm],device['kismet.device.base.frequency'])
        if 'kismet.device.base.signal' in device:
            lastSig = device['kismet.device.base.signal']['kismet.common.signal.last_signal']
            smetric.add_metric([ma,ssid,type,manuf,pd,pdm], lastSig)
        
        dataSize = device['kismet.device.base.datasize']
        packets = device['kismet.device.base.packets.total']
        
        pmetric.add_metric([ma,ssid,type,manuf,pd,pdm], packets)
        dmetric.add_metric([ma,ssid,type,manuf,pd,pdm], dataSize)
        
        if device['dot11.device']['dot11.device.bss_timestamp'] > 0:
            bsstimestamp = device['dot11.device']['dot11.device.bss_timestamp']/1000000
            bssmetric.add_metric([ma,ssid,type,manuf,pd,pdm],bsstimestamp)
        
        
    
    yield smetric
    yield dmetric
    yield pmetric
    yield bssmetric
    yield fmetric
    

if __name__ == "__main__":
  REGISTRY.register(KisCollector())
  start_http_server(http_server_port)
  while True: time.sleep(1)
