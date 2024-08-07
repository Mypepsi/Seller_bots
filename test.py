# import threading
# import time
from bots_libraries.sellpy.mongo import Mongo
# from queue import Queue, Empty
# import urllib.parse
from bots_libraries.sellpy.logs import Logs



# Список API ключів
# Приклад списку словників
# my_list = [
#     {'_id': 1, 'name': 'John', 'age': 30},
#     {'_id': 2, 'name': 'Jane', 'age': 25},
#     {'_id': 3, 'name': 'Doe', 'age': 22},
# ]
#
# # Значення для ідентифікації елемента та нові дані для оновлення
# identifier_key = '_id'
# identifier_value = 1
# new_data = {'name': 'John Doe', 'age': 31}
#
# # Оновлення елемента в списку
# for index, element in enumerate(my_list):
#     if element.get(identifier_key) == identifier_value:
#         my_list[index] = {**element, **new_data}
#         break
#
# # Вивід оновленого списку
# print(my_list)
# Приклад словника
mango = Mongo()
try:
    print(None < 10)

except:
    Logs.notify_except(mango.sellpy_tg_info, 'test error', '')


# class Test(Mongo):
#     def __init__(self):
#         super().__init__()
#
#         collection_name = f'history_ezra84rbgt'
#         self.acc_history_collection = self.get_collection(self.history, collection_name)
#         self.collection_info = self.get_all_docs_from_mongo_collection(self.acc_history_collection)
#         print(self.collection_info)
#
#
# test = Test()
# for doc in test.collection_info:
#     print(doc.get('transaction'))

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


