from flask import Response, request
from csv_data_server.config import get_config

CONFIG = get_config()

def check_auth() -> bool:
    auth = request.authorization 
    if auth is None:
        return False
    else:
        username = auth.username
        password = auth.password
        return username == CONFIG.username \
            and password == CONFIG.password

AUTH_FAILED_RESP = Response(
    "Authentication Failed.",
    401
)
