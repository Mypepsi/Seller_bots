import os
import time
import json
import uptime
import subprocess
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.mongo import Mongo


class Restarter(Mongo):
    def __init__(self, name):
        super().__init__(name)


    # region Restart Server
    def restart_server(self, tg_info, validity_time, global_time):
        Logs.log(f"Restart Server: thread are running", '')
        while True:
            try:
                time.sleep(global_time)
                server_uptime = uptime.uptime()
                if server_uptime > validity_time:
                    self.restart_server_command(tg_info)
            except Exception as e:
                self.restart_server_command(tg_info)
                Logs.notify_except(tg_info, f"Restart Server Global Error: {e}", '')

    def restart_server_command(self, tg_info):
        try:
            Logs.log(f"Server restarted", '')
            command = "sudo reboot"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            Logs.notify_except(tg_info, f"Restart Server: Error restarting Server: {e}", '')
    #endregion


    # region Restart Bots
    def restart_bots(self, tg_info, restart_info_bots, global_time):
        Logs.log(f"Restart Bots: thread are running", '')
        while True:
            try:
                time.sleep(global_time)
                command_json = "pm2 jlist"
                process_list = []
                result = subprocess.run(command_json, shell=True, check=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
                if result.stdout:
                    start_index = result.stdout.find("[")
                    if start_index != -1:
                        process_list = json.loads(result.stdout[start_index:])

                for bot_info in restart_info_bots:
                    bot_name = bot_info['name']
                    bot_validity_time = bot_info['restart validity time']
                    if process_list:
                        for process in process_list:
                            try:
                                process_name = process['name']
                                to_restart = process['pm2_env']['pm_uptime']
                                current_timestamp = int(time.time())
                                if ((bot_validity_time + to_restart / 1000) < current_timestamp and
                                        process_name == bot_name):
                                    self.restart_bot_command(tg_info, bot_name)
                                    break
                            except:
                                self.restart_bot_command(tg_info, bot_name)
                                break
            except Exception as e:
                Logs.notify_except(tg_info, f"Restart Bots Global Error: {e}", '')

    def restart_bot_command(self, tg_info, bot_name):
        try:
            command_restart = f'pm2 restart {bot_name} > /dev/null'
            Logs.log(f"Restart Bots: {bot_name} restarted", '')
            os.system(command_restart)
        except Exception as e:
            Logs.notify_except(tg_info, f"Restart Bots: Error restarting {bot_name}: {e}", '')
        time.sleep(10)
    #endregion