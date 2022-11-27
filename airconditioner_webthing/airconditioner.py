import time
import logging
import json
from threading import Thread
from time import sleep
from msmart.device import air_conditioning as ac
from datetime import datetime, timedelta



logging.basicConfig(level=logging.INFO)



class AirConditioner:

    def __init__(self, ip_address: str, id: int, max_program_duration: int = 20*60):
        self.max_program_duration = max_program_duration
        self.__device = ac(ip_address, id, 6444)
        self.__datetime_last_refresh = datetime.now() - timedelta(days=1)
        self.__program_deactivation_time = None
        self.__program_mode = 'cool'
        self.__program_target_temp = 23
        self.__listeners = set()
        Thread(target=self.__run_refresh, daemon=True).start()

    def __run_refresh(self):
        start = datetime.now()
        while True:
            try:
                sleep(6)
                elapsed_sec = (datetime.now() - start).total_seconds()
                threshold_sec = 5 if self.__device.power_state else (5*60)   # 5 sec or 5 min
                if elapsed_sec > threshold_sec:
                    start = datetime.now()
                    self.__sync()
            except Exception as e:
                logging.warning("error occurred by refreshing state " + str(e))
                sleep(30)

    def register_listener(self, listener):
        self.__listeners.add(listener)

    def __notify_listener(self):
        try:
            for listener in self.__listeners:
                listener()
        except Exception as e:
            pass

    def __sync(self, max_age_sec: int = 0, delay_sec: int = None):
        if delay_sec is not None:
            sleep(delay_sec)
        if (datetime.now() - self.__datetime_last_refresh).total_seconds() >= max_age_sec:
            logging.debug("executing sync")
            self.__datetime_last_refresh = datetime.now()
            self.__device.refresh()
            if not self.__device.power_state:
                self.__program_deactivation_time = None
            self.__notify_listener()

    def __apply(self):
        logging.debug("executing apply")
        self.__device.apply()
        Thread(target=self.__sync, kwargs={'delay_sec': 1}, daemon=True).start()

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
        return self.__device.target_temperature

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

    def __mode_to_id(self, mode:str) -> int:
        if mode == 'cool':
            return ac.operational_mode_enum.cool
        elif mode == 'heat':
            return ac.operational_mode_enum.heat
        elif mode == 'dry':
            return ac.operational_mode_enum.dry
        else:
            return ac.operational_mode_enum.auto

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
            raise Exception("unknown (" + str(self.__device.operational_mode) + ")")

    def __remaining_program_time(self) -> float:
        if self.__program_deactivation_time is None:
            return 0
        else:
            remaining_sec = (self.__program_deactivation_time - datetime.now()).total_seconds()
            if remaining_sec < 0:
                return 0
            else:
                return remaining_sec

    def program_run_util(self) -> str:
        time = self.__program_deactivation_time
        if time is None:
            return ""
        else:
            return time.strftime("%Y.%m.%dT%H:%M:%S")

    def program_mode(self) -> str:
        return self.__program_mode

    def set_program_mode(self, mode: str):
        self.__program_mode = mode
        self.__notify_listener()

    def program_target_temperature(self) -> int:
        return self.__program_target_temp

    def set_program_target_temperature(self, target_temp: int):
        self.__program_target_temp = target_temp
        self.__notify_listener()

    def set_program_run_util(self, end_date: str):
        time = datetime.strptime(end_date, "%Y.%m.%dT%H:%M:%S")
        if time > datetime.now():
            duration_sec = (time - datetime.now()).total_seconds()
            if duration_sec > self.max_program_duration:
                raise Exception("max program duration of " + str(self.max_program_duration) + " sec exceeded. Requested " + str(duration_sec) + " sec")
            else:
                self.__program_deactivation_time = time
                try:
                    self.__device.prompt_tone = True
                    self.__device.operational_mode = self.__mode_to_id(self.__program_mode)
                    self.__device.target_temperature = self.__program_target_temp
                    self.__device.power_state = True
                    self.__apply()
                    logging.info("starting air conditioner (mode: " + str(self.__program_mode) + " target temp: " + str(self.__program_target_temp) + "C, duration: " + str(self.__remaining_program_time()) + " sec)")
                finally:
                    Thread(target=self.__program_deactivation_watchdog, daemon=True).start()
        else:
            raise Exception(end_date + " is in the past. Will be ignored")

    def __program_deactivation_watchdog(self):
        time.sleep(5)
        self.__sync()
        if self.__program_deactivation_time is not None:
            time.sleep(self.__remaining_program_time())
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

