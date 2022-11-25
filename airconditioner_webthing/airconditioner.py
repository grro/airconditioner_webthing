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

    def set_operational_mode(self, mode: str):
        if mode == ac.operational_mode_enum.cool:
            self.__device.operational_mode = ac.operational_mode_enum.cool
            self.__apply()
        elif mode == ac.operational_mode_enum.heat:
            self.__device.operational_mode = ac.operational_mode_enum.heat
            self.__apply()
        elif mode == ac.operational_mode_enum.auto:
            self.__device.operational_mode = ac.operational_mode_enum.auto
            self.__apply()
        elif mode == ac.operational_mode_enum.dry:
            self.__device.operational_mode = ac.operational_mode_enum.dry
            self.__apply()
        else:
            logging.warning("unknown mode " + mode + " to be set. igmoring it")

    def remaining_minutes(self) -> float:
        return round(self.__remaining_operation_time_sec() / 60, 1)

    def run_util(self) -> str:
        time = self.__program_deactivation_time
        if time is None:
            return ""
        else:
            return time.strftime("%Y.%m.%dT%H:%M:%S")

    def set_run_util(self, end_date: str):
        self.__program_deactivation_time = datetime.strptime(end_date, "%Y.%m.%dT%H:%M:%S")
        try:
            self.__device.prompt_tone = True
            self.__device.power_state = True
            self.__apply()
            logging.info("starting air conditioner (target temp: " + str(self.target_temperature()) + "C, duration: " + str(round(self.remaining_minutes())) + " minutes)")
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

