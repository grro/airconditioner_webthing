from webthing import (SingleThing, Property, Thing, Value, WebThingServer)
import logging
import tornado.ioloop
from airconditioner_webthing.airconditioner import AirConditioner



class AirConditionerThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing
    def __init__(self, description: str, ac: AirConditioner, name: str):
        Thing.__init__(
            self,
            'urn:dev:ops:AirConditioner-1',
            ('AirConditioner ' + name).strip(),
            ['MultiLevelSensor'],
            description
        )

        self.ac = ac

        self.outdoor_temperature = Value(ac.outdoor_temperature())
        self.add_property(
            Property(self,
                     'outdoor_temperature',
                     self.outdoor_temperature,
                     metadata={
                         'title': 'Outdoor Temperature',
                         "type": "integer",
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
                         "type": "integer",
                         'description': 'The indoor temperature',
                         'readOnly': True,
                     }))

        self.target_temperature = Value(ac.target_temperature())
        self.add_property(
            Property(self,
                     'target_temperature',
                     self.target_temperature,
                     metadata={
                         'title': 'Target Temperature',
                         "type": "integer",
                         'description': 'The target temperature',
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
                         'description': 'The operational mode (supported: heat, cool, auto, dry)',
                         'readOnly': True,
                     }))

        self.fan_speed = Value(ac.fan_speed())
        self.add_property(
            Property(self,
                     'fan_speed',
                     self.fan_speed,
                     metadata={
                         'title': 'Fan Speed',
                         "type": "integer",
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

        self.program_mode = Value(ac.program_mode(), ac.set_program_mode)
        self.add_property(
            Property(self,
                     'program_mode',
                     self.program_mode,
                     metadata={
                         'title': 'Program mode',
                         "type": "string",
                         'description': 'The program operational mode (supported: heat, cool, auto, dry)',
                         'readOnly': False,
                     }))

        self.program_target_temperature = Value(ac.program_target_temperature(), ac.set_program_target_temperature)
        self.add_property(
            Property(self,
                     'program_target_temperature',
                     self.program_target_temperature,
                     metadata={
                         'title': 'Program target temperature',
                         "type": "number",
                         'description': 'The program target temp',
                         'readOnly': False,
                     }))

        self.program_run_util = Value(ac.program_run_util(), ac.set_program_run_util)
        self.add_property(
            Property(self,
                     'program_run_util',
                     self.program_run_util,
                     metadata={
                         'title': 'program run util',
                         "type": "string",
                         'description': 'the end time of air conditioner execution (format: %Y.%m.%dT%H:%M:%)',
                         'readOnly': False,
                     }))

        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ac.register_listener(self.on_value_changed)

    def on_value_changed(self):
        self.ioloop.add_callback(self.__on_value_changed)

    def __on_value_changed(self):
        self.power.notify_of_external_update(self.ac.power())
        self.operational_mode.notify_of_external_update(self.ac.operational_mode())
        self.target_temperature.notify_of_external_update(self.ac.target_temperature())
        self.indoor_temperature.notify_of_external_update(self.ac.indoor_temperature())
        self.outdoor_temperature.notify_of_external_update(self.ac.outdoor_temperature())
        self.fan_speed.notify_of_external_update(self.ac.fan_speed())
        self.program_target_temperature.notify_of_external_update(self.ac.program_target_temperature())
        self.program_mode.notify_of_external_update(self.ac.program_mode())
        self.program_run_util.notify_of_external_update(self.ac.program_run_util())


def run_server(description: str, port: int, ip_address: str, id: int, name:str):
    ac = AirConditioner(ip_address, id)
    ac_thing = AirConditionerThing(description, ac, name)
    server = WebThingServer(SingleThing(ac_thing), port=port, disable_host_validation=True)
    logging.info('running webthing server http://localhost:' + str(port))
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping webthing server')
        server.stop()
        logging.info('done')

