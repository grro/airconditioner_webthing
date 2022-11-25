import time
import logging
import json
from threading import Thread
from time import sleep
from msmart.device import air_conditioning as ac
from datetime import  datetime, timedelta



logging.basicConfig(level=logging.INFO)



class AirConditioner:

    def __init__(self, ip_address: str, id: int):
        self.__device = ac(ip_address, id, 6444)
        self.__datetime_last_refresh = datetime.now() - timedelta(days=1)
        self.__program_deactivation_time = None
        self.__cooling_temp = 19
        self.__heating_temp = 24
        self.__listeners = set()
        Thread(target=self.__run_refresh, daemon=True).start()

    def __run_refresh(self):
        start = datetime.now()
        while True:
            sleep(6)
            wait_time_sec = 5 if self.power else (6*60)
            if (datetime.now() - start).total_seconds() > wait_time_sec:
                start = datetime.now()
                try:
                    self.__sync(max_age_sec=10)
                except Exception as e:
                    pass

    def register_listener(self, listener):
        self.__listeners.add(listener)

    def __notify_listener(self):
        try:
            for listener in self.__listeners:
                listener()
        except Exception as e:
            pass

    def __sync(self, max_age_sec: int = 0):
        if (datetime.now() - self.__datetime_last_refresh).total_seconds() >= max_age_sec:
            self.__datetime_last_refresh = datetime.now()
            self.__device.refresh()
            if not self.__device.power_state:
                self.__program_deactivation_time = None
            self.__notify_listener()

    def __apply(self):
        self.__device.apply()
        Thread(target=self.__sync, daemon=True).start()

    def cooling_temp(self) -> int:
        return int(round(self.__cooling_temp))

    def set_cooling_temp(self, temp: int):
        self.__cooling_temp = temp

    def heating_temp(self) -> int:
        return int(round(self.__heating_temp))

    def set_heating_temp(self, temp: int):
        self.__heating_temp = temp

    def __remaining_operation_time_sec(self) -> int:
        if self.__program_deactivation_time is None:
            return 0
        else:
            return int(round((self.__program_deactivation_time - datetime.now()).total_seconds()))

    def power(self) -> bool:
        self.__sync(max_age_sec=3)
        return self.__device.power_state

    def set_power(self, is_on: bool):
        logging.info("setting power = " + str(is_on))
        self.__device.power_state = is_on
        self.__device.prompt_tone = True
        self.__apply()

    def target_temperature(self) -> int:
        self.__sync(max_age_sec=3)
        return int(round(self.__device.target_temperature))

    def set_target_temperature(self, target_temp: int):
        self.__device.target_temperature = target_temp
        self.__apply()

    def indoor_temperature(self) -> int:
        self.__sync(max_age_sec=3)
        return int(round(self.__device.indoor_temperature,0))

    def outdoor_temperature(self) -> int:
        self.__sync(max_age_sec=3)
        return int(round(self.__device.outdoor_temperature,0))

    def fan_speed(self) -> int:
        self.__sync(max_age_sec=3)
        return int(self.__device.fan_speed)

    def operational_mode(self) -> str:
        self.__sync(max_age_sec=3)
        if self.__device.operational_mode == ac.operational_mode_enum.cool:
            return "cool"
        elif self.__device.operational_mode == ac.operational_mode_enum.heat:
            return "heat"
        elif self.__device.operational_mode == ac.operational_mode_enum.auto:
            return "auto"
        elif self.__device.operational_mode == ac.operational_mode_enum.dry:
            return "dry"
        else:
            return "unknown (" + str(self.__device.operational_mode) + ")"

    def __activate_program_until(self, end_date: datetime, target_temperature: float, operational_mode: int):
        self.__program_deactivation_time = end_date
        try:
            self.__device.prompt_tone = True
            self.__device.power_state = True
            self.__device.target_temperature = target_temperature
            self.__device.operational_mode = operational_mode
            self.__apply()
            logging.info("starting air conditioner (target temp: " + str(target_temperature) + "C, duration: " + str(round(self.__remaining_operation_time_sec())) + " sec)")
        finally:
            Thread(target=self.__program_deactivation_watchdog, daemon=True).start()

    def __program_deactivation_watchdog(self):
        time.sleep(5)
        self.__sync()
        if self.__program_deactivation_time is not None:
            time.sleep(self.__remaining_operation_time_sec())
            logging.info("program completed. Stopping device")
            self.set_power(False)

            # retry if not deactivated
            self.__sync()
            if self.__program_deactivation_time is None:
                logging.info("device stopped")
            else:
                sleep(60)
                Thread(target=self.__program_deactivation_watchdog, daemon=True).start()

    def cooling_remaining_minutes(self) -> int:
        if self.__device.operational_mode == ac.operational_mode_enum.cool:
            return int(round(self.__remaining_operation_time_sec() / 60, 1))
        else:
            return 0

    def set_cooling_remaining_minutes(self, duration: int):
        self.__activate_program_until(datetime.now() + timedelta(minutes=duration), self.__cooling_temp, ac.operational_mode_enum.cool)

    def heating_remaining_minutes(self) -> int:
        if self.__device.operational_mode == ac.operational_mode_enum.heat:
            return int(round(self.__remaining_operation_time_sec() / 60, 1))
        else:
            return 0

    def set_heating_remaining_minutes(self, duration: int):
        self.__activate_program_until(datetime.now() + timedelta(minutes=duration), self.__heating_temp, ac.operational_mode_enum.heat)

    def __str__(self):
        self.__sync()
        return json.dumps({
                    'id': self.__device.id,
                    'name': self.__device.ip,
                    'power_state': self.__device.power_state,
                    'prompt_tone': self.__device.prompt_tone,
                    'target_temperature': self.__device.target_temperature,
                    'operational_mode': self.__device.operational_mode,
                    'fan_speed': self.__device.fan_speed,
                    'swing_mode': self.__device.swing_mode,
                    'eco_mode': self.__device.eco_mode,
                    'turbo_mode': self.__device.turbo_mode,
                    'fahrenheit': self.__device.fahrenheit,
                    'indoor_temperature': self.__device.indoor_temperature,
                    'outdoor_temperature': self.__device.outdoor_temperature
                }, indent=2)

