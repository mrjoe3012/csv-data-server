from flask import Flask, jsonify, request, send_file
from csv_data_server.config import get_config
from csv_data_server.file_system import FileSystem
from csv_data_server.authentication import check_auth, AUTH_FAILED_RESP
from csv_data_server.models import (
    AddRowsReq
)
from pydantic import ValidationError

CONFIG = get_config()
APP = Flask(__name__)
FILE_SYSTEM = FileSystem()

@APP.route('/ls', methods=['GET'])
def ls():
    if not check_auth():
        return AUTH_FAILED_RESP
    try:
        files = FILE_SYSTEM.ls()
    except RuntimeError as e:
        return f"Bad request: {e}", 400
    return jsonify({'files' : files})    

@APP.route('/add-rows', methods=['POST'])
def add_rows():
    if not check_auth():
        return AUTH_FAILED_RESP
    data = request.get_json()
    if not data:
        return "Bad request", 400
    try:
        req_data = AddRowsReq(**data)
    except ValidationError as e:
        return f"Bad request. {e}", 400
    try:
        FILE_SYSTEM.add_rows(
            req_data.filename,
            req_data.rows,
            headers=req_data.headers
        )
    except RuntimeError as e:
        return f'Bad request. {e}', 400
    return "", 200

@APP.route('/get-file', methods=['GET'])
def get_file():
    if not check_auth():
        return AUTH_FAILED_RESP
    params = request.args
    filename = params.get('filename', None)
    if filename is None:
        return "Bad request. Missing filename.", 400
    try:
        filepath = FILE_SYSTEM.get_file(filename)
    except RuntimeError as e:
        return f"Bad request: {e}"
    return send_file(
        filepath,
        as_attachment=True,
        mimetype='text/csv',
        download_name=filename
    )

def main():
    APP.run(
        host=CONFIG.host,
        port=CONFIG.port,
        debug=CONFIG.debug
    )

if __name__ == '__main__':
    main()
