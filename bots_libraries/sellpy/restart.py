import os
import time
import json
import uptime
import subprocess
from bots_libraries.sellpy.logs import Logs
from bots_libraries.sellpy.mongo import Mongo


class Restarter(Mongo):
    def __init__(self):
        super().__init__()



    # region restart server
    def restart_server(self, validity_time, global_time):
        while True:
            try:
                time.sleep(global_time)
                server_uptime = uptime.uptime()
                if server_uptime > validity_time:
                    self.restart_server_command()
            except Exception as e:
                Logs.notify_except(self.sellpy_tg_info, f'Error getting Server uptime: {e}', '')
                self.restart_server_command()

    def restart_server_command(self):
        try:
            Logs.log(f"Server Rebooted", '')
            command = "sudo reboot"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error restarting Server: {e}", '')
    #endregion



    # region restart bots
    def restart_bots(self, restart_info_bots, global_time):
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

            except Exception as e:
                process_list = None
                Logs.notify_except(self.sellpy_tg_info, f"No output from pm2 jlist: {e}", '')
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
                                    self.restart_bot_command(bot_name)
                                    break
                            except:
                                self.restart_bot_command(bot_name)
                                break
            except Exception as e:
                Logs.notify_except(self.sellpy_tg_info, f"Error during restart Bots: {e}", '')

    def restart_bot_command(self, bot_name):
        try:
            command_restart = f'pm2 restart {bot_name} > /dev/null'
            Logs.log(f"{bot_name} Restarted", '')
            os.system(command_restart)

            time.sleep(5)
        except Exception as e:
            Logs.notify_except(self.sellpy_tg_info, f"Error restarting {bot_name}: {e}", '')
    #endregion
