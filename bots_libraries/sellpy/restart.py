import os
import time
import json
import uptime
import subprocess
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.mongo import Mongo


class Restarter(Mongo):
    def __init__(self, main_tg_info):
        super().__init__(main_tg_info)

    # region Restart Server
    def restart_server(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Restart Server: thread are running", '')
        while True:
            time.sleep(self.restart_server_global_time)
            try:
                server_uptime = uptime.uptime()
                if server_uptime > self.restart_server_validity_time:
                    self.restart_server_command()
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Server Global Error: {e}", '')

    def restart_server_command(self):
        try:
            Logs.log(f"Server restarted", '')
            command = "sudo reboot"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Restart Server: Error restarting Server: {e}", '')
    # endregion

    # region Restart Bots
    def restart_bots(self):  # Global Function (class_for_many_functions)
        Logs.log(f"Restart Bots: thread are running", '')
        while True:
            time.sleep(self.restart_bots_global_time)
            try:
                command_json = "pm2 jlist"
                process_list = []
                result = subprocess.run(command_json, shell=True, check=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
                if result.stdout:
                    start_index = result.stdout.find("[")
                    if start_index != -1:
                        process_list = json.loads(result.stdout[start_index:])

                if process_list:
                    for bot_info in self.restart_bots_name:
                        bot_name = bot_info['name']
                        bot_validity_time = bot_info['restart validity time']
                        for process in process_list:
                            try:
                                process_name = process['name']
                                to_restart = process['pm2_env']['pm_uptime']
                                current_timestamp = int(time.time())
                                if ((process_name == bot_name
                                     and bot_validity_time + to_restart / 1000) < current_timestamp):
                                    self.restart_bot_command(bot_name)
                                    break
                            except:
                                self.restart_bot_command(bot_name)
                                break
            except Exception as e:
                Logs.notify_except(self.tg_info, f"Restart Bots Global Error: {e}", '')

    def restart_bot_command(self, bot_name):
        try:
            command_restart = f'pm2 restart {bot_name} > /dev/null'
            Logs.log(f"Restart Bots: {bot_name} restarted", '')
            os.system(command_restart)
        except Exception as e:
            Logs.notify_except(self.tg_info, f"Restart Bots: Error restarting {bot_name}: {e}", '')
        time.sleep(10)
    #endregion