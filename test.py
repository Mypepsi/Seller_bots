import jwt
jwt_api_key = jwt.encode(
                    {'userId': '65c8d273c84b5865c1d60b17'},
                    '1c3754ebfc45b4f492ea0ada263d31b3082b4e70e7587b1459d6a15520b0f090',
                    algorithm="HS256"
                )

print(jwt_api_key)