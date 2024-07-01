import subprocess
import os
import time
import json
import uptime
from bots_libraries.base_info.mongo import Mongo
from bots_libraries.base_info.logs import Logs


class Restarter(Mongo):
    def __init__(self):
        super().__init__()

    def schedule_restart_server(self, validity_time, global_time):
        while True:
            try:
                time.sleep(global_time)
                server_uptime = uptime.uptime()
                if server_uptime > validity_time:
                    self.restart_server()
            except Exception as e:
                Logs.log(f'Get server uptime Error: {e}')
                self.restart_server()

    def schedule_restart_bots(self, restart_info_bots, global_time):
        while True:
            command_json = "pm2 jlist"
            process_list = []
            try:
                time.sleep(global_time)
                result = subprocess.run(command_json, shell=True, check=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
                if result.stdout:
                    start_index = result.stdout.find("[")
                    if start_index != -1:
                        process_list = json.loads(result.stdout[start_index:])

            except Exception:
                process_list = None
                Logs.log("No output from pm2 jlist command")
            try:
                for bot_info in restart_info_bots:
                    bot_name = bot_info['name']
                    bot_validity_time = bot_info['restart validity time']
                    if process_list is not None:
                        for process in process_list:
                            try:
                                process_name = process['name']
                                to_restart = process['pm2_env']['pm_uptime']
                                current_timestamp = int(time.time())
                                if ((bot_validity_time + to_restart / 1000) < current_timestamp and
                                        process_name == bot_name):
                                    self.restart_bot(bot_name)
                                    break
                            except:
                                self.restart_bot(bot_name)
                                break
            except Exception as e:
                Logs.log(f"Error during bot restart - 2: {e}")

    def restart_server(self):
        try:
            Logs.log(f"Server Rebooted")
            command = "sudo reboot"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            Logs.log(f"Error during system restart: {e}")

    def restart_bot(self, bot_name):
        try:
            command_restart = f'pm2 restart {bot_name} > /dev/null'
            Logs.log(f"{bot_name} Restarted")
            os.system(command_restart)

            time.sleep(5)
        except Exception as e:
            Logs.log(f"Error restarting {bot_name}: {e}")
