import threading
import time
from bots_libraries.base_info.mongo import Mongo
from queue import Queue, Empty

# Список API ключів
api_keys = ["api_key_1", "api_key_2", "api_key_3", "api_key_4"]

# Список хешнеймів
hash_names = [
    "hashname1", "hashname2", "hashname3", "hashname4", "hashname5",
    "hashname6", "hashname7", "hashname8", "hashname9", "hashname10",
    "hashname11", "hashname12", "hashname13", "hashname14", "hashname15",
    "hashname16", "hashname17", "hashname18", "hashname19", "hashname20",
    "hashname21", "hashname22", "hashname23", "hashname24", "hashname25",
    "hashname26", "hashname27", "hashname28", "hashname29", "hashname30"
]

# Список API ключів
class Test(Mongo):
    def test(self):
        self.acc_history_collection = self.get_collection(self.accs, 'account_data')
        collection_info = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
        print(collection_info)


# test = Test()
# test.test()
print(3)
items = [1, 4, 4, 5.2, 19.1, 19.1, 'fdfd', 'wewef', 'qweqweqwe', 'qweqweqwe', '213123']


items = list(set(items))
print(items)
#     def parsing_prices(self, api_key, hash_queue, results, results_lock):
#         while True:
#             try:
#                 time.sleep(1.5)
#
#                 hash_name = hash_queue.get_nowait()
#                 pr = f"{hash_name}  {api_key}"
#                 print(pr)
#                 with results_lock:
#                     results.append(pr)
#                 hash_queue.task_done()
#             except Empty:
#                 break
#             except Exception as e:
#                 if 'hash_name' in locals():
#                     hash_queue.task_done()
#
#     def threads_to_parsing(self, items, api_keys):
#         threads = []
#         results = []
#         results_lock = threading.Lock()
#         hash_queue = Queue()
#
#         for hash_name in items:
#             hash_queue.put(hash_name)
#
#         for api_key in api_keys:
#             time.sleep(1)
#             thread = threading.Thread(target=self.parsing_prices,
#                                       args=(api_key, hash_queue, results, results_lock))
#             thread.start()
#             threads.append(thread)
#
#         for thread in threads:
#             thread.join()
#         print(results)
#
#
# test = Test()
# test.threads_to_parsing(hash_names, api_keys)



