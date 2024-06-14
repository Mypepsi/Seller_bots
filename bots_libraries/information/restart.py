import subprocess
import os
import time
import json
import uptime
from bots_libraries.information.mongo import Mongo
from bots_libraries.information.logs import Logs


class Restarter(Mongo):
    def __init__(self):
        super().__init__()

    def get_server_uptime(self, validity_time, global_time):
        while True:
            try:
                server_uptime = uptime.uptime()
                if server_uptime > validity_time:
                    self.restart_server()
            except Exception as e:
                Logs.log(f'Get server uptime Error: {e}')
            time.sleep(global_time)

    def restart_bots(self, restart_info_bots, global_time):
        while True:
            try:
                for bot_info in restart_info_bots:
                    bot_name = bot_info['name']
                    bot_validity_time = bot_info['restart validity time']
                    process_list = []
                    command_json = "pm2 jlist"
                    result = subprocess.run(command_json, shell=True, check=True, capture_output=True, text=True)
                    if result.stdout:
                        start_index = result.stdout.find("[")
                        if start_index != -1:
                            process_list = json.loads(result.stdout[start_index:])

                        for process in process_list:
                            to_restart = process['pm2_env']['pm_uptime']
                            current_timestamp = int(time.time())
                            if (bot_validity_time + to_restart / 1000) < current_timestamp and process['name'] == bot_name: #bot_name = 'Creator'
                                try:
                                    command_restart = f'pm2 restart bot_name'
                                    os.system(command_restart)
                                except subprocess.CalledProcessError as e:
                                    Logs.log(f"Error restarting {bot_name}: {e}")
                                time.sleep(5)
                    else:
                        Logs.log("No output from pm2 jlist command")
            except json.JSONDecodeError as e:
                Logs.log(f"Error parsing JSON output: {e}")
            except Exception as e:
                Logs.log(f"Error during system restart: {e}")
            time.sleep(global_time)



    def restart_server(self):
        command = "sudo reboot"
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            Logs.log(f"Error during system restart: {e}")


