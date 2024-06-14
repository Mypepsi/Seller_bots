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

    def schedule_restart_server(self, validity_time, global_time):
        while True:
            try:
                server_uptime = uptime.uptime()
                if server_uptime > validity_time:
                    self.restart_server()
            except Exception as e:
                Logs.log(f'Get server uptime Error: {e}')
                self.restart_server()
            time.sleep(global_time)

    def schedule_restart_bots(self, restart_info_bots, global_time):
        while True:
            try:
                for bot_info in restart_info_bots:
                    bot_name = bot_info['name']
                    bot_validity_time = bot_info['restart validity time']
                    process_list = []
                    command_json = "pm2 jlist"
                    try:
                        result = subprocess.run(command_json, shell=True, check=True, capture_output=True, text=True)
                        if result.stdout:
                            start_index = result.stdout.find("[")
                            if start_index != -1:
                                process_list = json.loads(result.stdout[start_index:])

                            for process in process_list:
                                try:
                                    to_restart = process['pm2_env']['pm_uptime']
                                except:
                                    to_restart = 0
                                current_timestamp = int(time.time())
                                if (bot_validity_time + to_restart / 1000) < current_timestamp and process['name'] == bot_name: #bot_name = 'Creator'
                                    self.restart_bot(bot_name)
                                    time.sleep(5)
                        else:
                            Logs.log("No output from pm2 jlist command")
                    except Exception as e:
                        Logs.log(f"Error during bot restart - 1: {e}")
                        self.restart_bot(bot_name)
                        time.sleep(5)
            except Exception as e:
                Logs.log(f"Error during bot restart - 2: {e}")
            time.sleep(global_time)

    def restart_bot(self, bot_name):
        try:
            command_restart = f'pm2 restart bot_name'
            Logs.log(f"{bot_name} will be restarted now")
            os.system(command_restart)
        except subprocess.CalledProcessError as e:
            Logs.log(f"Error restarting {bot_name}: {e}")

    def restart_server(self):
        try:
            Logs.log(f"Server will be restarted now")
            command = "sudo reboot"
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            Logs.log(f"Error during system restart: {e}")


