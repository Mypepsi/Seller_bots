import jwt

another_jwt_api_key = jwt.encode(
                        {'userId': '66a7b34569550ca2fe0dc369'},
                        '12964f1663a2b36fc84ac878603dc13e41389fe32fb61e403649f9a797690e2d',
                        algorithm="HS256"
                    )

print(another_jwt_api_key)
