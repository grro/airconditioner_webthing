from webthing import (SingleThing, Property, Thing, Value, WebThingServer)
import logging
import tornado.ioloop
from airconditioner_webthing.airconditioner import AirConditioner



class AirConditionerThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing
    def __init__(self, description: str, ac: AirConditioner):
        Thing.__init__(
            self,
            'urn:dev:ops:AirConditioner-1',
            'AirConditioner',
            ['MultiLevelSensor'],
            description
        )

        self.ac = ac

        self.power = Value(ac.power())
        self.add_property(
            Property(self,
                     'power',
                     self.power,
                     metadata={
                         'title': 'Power',
                         "type": "boolean",
                         'description': 'Power',
                         'readOnly': False,
                     }))

        self.target_temperature = Value(ac.target_temperature(), ac.set_target_temperature)
        self.add_property(
            Property(self,
                     'target_temperature',
                     self.target_temperature,
                     metadata={
                         'title': 'Target Temperature',
                         "type": "float",
                         'description': 'The target temperature',
                         'readOnly': False,
                     }))

        self.heating_temp = Value(ac.heating_temp(), ac.set_heating_temp)
        self.add_property(
            Property(self,
                     'heating_temp',
                     self.heating_temp,
                     metadata={
                         'title': 'Heating Temperature',
                         "type": "float",
                         'description': 'The target temperature in heating mode',
                         'readOnly': False,
                     }))

        self.cooling_temp = Value(ac.cooling_temp(), ac.set_cooling_temp)
        self.add_property(
            Property(self,
                     'cooling_temp',
                     self.cooling_temp,
                     metadata={
                         'title': 'Cooling Temperature',
                         "type": "float",
                         'description': 'The target temperature in cooling mode',
                         'readOnly': False,
                     }))

        self.outdoor_temperature = Value(ac.outdoor_temperature())
        self.add_property(
            Property(self,
                     'outdoor_temperature',
                     self.outdoor_temperature,
                     metadata={
                         'title': 'Outdoor Temperature',
                         "type": "float",
                         'description': 'The outdoor temperature',
                         'readOnly': True,
                     }))

        self.indoor_temperature = Value(ac.indoor_temperature())
        self.add_property(
            Property(self,
                     'indoor_temperature',
                     self.indoor_temperature,
                     metadata={
                         'title': 'Indoor Temperature',
                         "type": "float",
                         'description': 'The indoor temperature',
                         'readOnly': True,
                     }))

        self.operational_mode = Value(ac.operational_mode())
        self.add_property(
            Property(self,
                     'operational_mode',
                     self.operational_mode,
                     metadata={
                         'title': 'Operational mode',
                         "type": "string",
                         'description': 'The operational mode',
                         'readOnly': True,
                     }))

        self.fan_speed = Value(ac.fan_speed())
        self.add_property(
            Property(self,
                     'fan_speed',
                     self.fan_speed,
                     metadata={
                         'title': 'Fan Speed',
                         "type": "int",
                         'description': 'The fan speed',
                         'readOnly': True,
                     }))

        self.power = Value(ac.power(), ac.set_power)
        self.add_property(
            Property(self,
                     'power',
                     self.power,
                     metadata={
                         'title': 'Power',
                         "type": "boolean",
                         'description': 'Power',
                         'readOnly': False,
                     }))

        self.cooling_remaining_minutes = Value(ac.cooling_remaining_minutes(), ac.set_cooling_remaining_minutes)
        self.add_property(
            Property(self,
                     'cooling_remaining_minutes',
                     self.cooling_remaining_minutes,
                     metadata={
                         'title': 'Cooling remaining minutes',
                         "type": "number",
                         'description': 'The remaining cooling duration in minutes',
                         'readOnly': False,
                     }))

        self.heating_remaining_minutes = Value(ac.heating_remaining_minutes(), ac.set_heating_remaining_minutes)
        self.add_property(
            Property(self,
                     'heating_remaining_minutes',
                     self.heating_remaining_minutes,
                     metadata={
                         'title': 'Heating remaining minutes',
                         "type": "number",
                         'description': 'The remaining heating duration in minutes',
                         'readOnly': False,
                     }))

        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ac.register_listener(self.on_value_changed)

    def on_value_changed(self):
        self.ioloop.add_callback(self.__on_value_changed)

    def __on_value_changed(self):
        self.cooling_remaining_minutes.notify_of_external_update(self.ac.cooling_remaining_minutes())
        self.heating_remaining_minutes.notify_of_external_update(self.ac.heating_remaining_minutes())
        self.power.notify_of_external_update(self.ac.power())
        self.cooling_temp.notify_of_external_update(self.ac.cooling_temp())
        self.heating_temp.notify_of_external_update(self.ac.heating_temp())
        self.operational_mode.notify_of_external_update(self.ac.operational_mode())
        self.target_temperature.notify_of_external_update(self.ac.target_temperature())
        self.indoor_temperature.notify_of_external_update(self.ac.indoor_temperature())
        self.outdoor_temperature.notify_of_external_update(self.ac.outdoor_temperature())
        self.fan_speed.notify_of_external_update(self.ac.fan_speed())


def run_server(description: str, port: int, ip_address: str, id: int):
    ac = AirConditioner(ip_address, id)
    ac_thing = AirConditionerThing(description, ac)
    server = WebThingServer(SingleThing(ac_thing), port=port, disable_host_validation=True)
    logging.info('running webthing server http://localhost:' + str(port))
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping webthing server')
        server.stop()
        logging.info('done')

