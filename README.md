# airconditioner_webthing
An airconditioner web thing connector

This project provides a [webthing API](https://iot.mozilla.org/wot/) to Midea air conditioners

The airconditioner_webthing package exposes a http webthing endpoint which supports controlling the air conditioner via http. E.g.
```
# webthing has been started on host 192.168.0.23

curl http://192.168.0.23:7122/properties 

{
   "outdoor_temperature": 4,
   "indoor_temperature": 22,
   "target_temperature": 23,
   "operational_mode": "heat",
   "fan_speed": 102,
   "power": false,
   "run_util": ""
}
```

To install this software you may use [PIP](https://realpython.com/what-is-pip/) package manager such as shown below
```
sudo pip install airconditioner_webthing
```

After this installation you may start the webthing http endpoint inside your python code or via command line using
```
sudo aircon --command listen --port 7122 --ip 10.31.33.90 --id 957548654462565 
```
Here, the webthing API will be bound to the local port 7122. Additionally, the ip address of the air conditioner has to be set 
as well as the device id of the air conditioner. To discovery the device id you may use [midea-msmart](https://github.com/mac-zhou/midea-msmart) library as shon below
```
midea-discover -a YOUR_ACCOUNT -p YOUR_PASSWORD
```

Alternatively to the *listen* command, you can use the *register* command to register and start the webthing service as systemd unit.
By doing this the webthing service will be started automatically on boot. Starting the server manually using the *listen* command is no longer necessary.
```
sudo aircon --command register --port 7122 --ip 10.31.33.90 --id 957548654462565 
```  
