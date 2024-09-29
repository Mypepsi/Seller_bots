import json

socket_response = '{"name":"pong","data":{"msg":"1"}}'


print(json.loads(socket_response))
