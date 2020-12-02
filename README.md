# Kismet Exporter

Using [python-kismet-rest](https://github.com/kismetwireless/python-kismet-rest/) to export some stats to prometheus so that we can graph things 

this is just me playing so things might be massively wrong, right now this is me having fun with monitoring the wifi enviroment at my house. I live near a main road so it is fun to see how many Porsch hot spots go by or get a general idea of how busy things are by seeing how many devices are about. 

this will probably expand as I figure more things out, its likely also way ineffecnt to maybe just querying the kismet DB directly

# metrics exported 

- metrics 
	- kismet_device_signal_strength signel strength of devices seen  (Guage) 
	- kismet_device_data_seen amount of data seen for each device (Counter)
	- kismet_device_packets_seen total packets seen for a device (Counter)
- labels
	- mac MAC address of the device 
	- ssid The ssid that the device is associated with / commonname (more than one ssid is seprated by pipes) 
	- wifi_type the wifi type of the device Wifi AP, Wi-Fi Ad-Hoc, Wi-Fi Bridged Wifi Client Wifi Device
	- manuf the manufactuer of the device if known 

# Usage 

use the docker compose file, this is just set up to run the exporter. 


## env variables

copy kismet_exporter.env.example to kismet_exporter.env with the correct kismet information  


## Example Prometheus config assuming promethues runs on the same host as the docker container.  
```
- job_name: kismet-exporter
  static_configs: 
  	-targets: 
  	   - localhost:8501 
```


