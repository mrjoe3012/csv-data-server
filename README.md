# CSV Data Server

A small Flask web server for managing CSV files over HTTP.

The server was originally created to ingest data from an ESP32-based temperature monitor, but it can be used by any HTTP client that can authenticate with the configured credentials.

Clients can:

* List available CSV/data files
* Append rows to CSV files
* Download CSV files
* Automatically create new CSV files when rows are added

Authentication is handled using a fixed username/password configured through a `.env` file.

## Features

* Simple Flask HTTP server
* Username/password authentication
* Configuration through environment variables / `.env`
* CSV file storage on the local filesystem
* Automatic creation of the configured data directory
* Automatic creation of CSV files
* Optional CSV headers when creating a new file
* Protection against filesystem path traversal
* JSON API suitable for small devices such as an ESP32

## Requirements

* Python 3.9+
* Flask
* Pydantic
* Pydantic Settings

Install the Python dependencies with:

```bash
pip install flask pydantic pydantic-settings python-dotenv
```

If the project provides a `requirements.txt`, the recommended approach is instead:

```bash
pip install -r requirements.txt
```

## Configuration

Configuration is provided using environment variables prefixed with `DATA_SERVER_`.

The server also automatically loads variables from a `.env` file in the current working directory.

The configuration is defined using Pydantic Settings:

```python
class Config(BaseSettings):
    username: str
    password: str
    host: str
    port: int
    debug: bool
    root_dir: str

    model_config = SettingsConfigDict(
        env_prefix='DATA_SERVER_',
        env_file='.env'
    )
```

### `.env`

A typical `.env` file looks like:

```dotenv
DATA_SERVER_USERNAME=myuser
DATA_SERVER_PASSWORD=mysecretpassword
DATA_SERVER_HOST=0.0.0.0
DATA_SERVER_PORT=5000
DATA_SERVER_DEBUG=false
DATA_SERVER_ROOT_DIR=./data
```

The values have the following meanings:

| Variable               | Description                             | Example            |
| ---------------------- | --------------------------------------- | ------------------ |
| `DATA_SERVER_USERNAME` | Username used for authentication        | `myuser`           |
| `DATA_SERVER_PASSWORD` | Password used for authentication        | `mysecretpassword` |
| `DATA_SERVER_HOST`     | Network interface the server listens on | `0.0.0.0`          |
| `DATA_SERVER_PORT`     | HTTP port                               | `5000`             |
| `DATA_SERVER_DEBUG`    | Enable Flask debug mode                 | `false`            |
| `DATA_SERVER_ROOT_DIR` | Directory in which CSV files are stored | `./data`           |

Keep the `.env` file out of source control, particularly if it contains a real password.

For example, add this to `.gitignore`:

```gitignore
.env
data/
```

## Running the Server

Once the environment has been configured, the server can be started with:

```bash
python main.py
```

For example, with:

```dotenv
DATA_SERVER_HOST=0.0.0.0
DATA_SERVER_PORT=5000
```

the server will be available on:

```text
http://<server-ip>:5000
```

If the server is running locally:

```text
http://localhost:5000
```

### Flask development server

The application currently uses:

```python
APP.run(
    host=CONFIG.host,
    port=CONFIG.port,
    debug=CONFIG.debug
)
```

This uses Flask's built-in development server. It is suitable for simple/local deployments, such as a small home sensor project.

For a production deployment exposed to an untrusted network, consider running Flask through a production WSGI server such as Gunicorn instead.

For example:

```bash
gunicorn -b 0.0.0.0:5000 main:APP
```

## File Storage

CSV files are stored underneath the directory specified by:

```dotenv
DATA_SERVER_ROOT_DIR=./data
```

If the directory does not exist when the server starts, it is automatically created.

For example:

```text
project/
├── main.py
├── .env
└── data/
    ├── temperature.csv
    ├── humidity.csv
    └── sensor-01.csv
```

The server does not require files to be created manually. When a file is referenced by `/add-rows` or `/get-file`, it can be created automatically if it does not already exist.

### File paths

Filenames supplied by clients are resolved relative to `DATA_SERVER_ROOT_DIR`.

The server checks that the resulting path remains inside the configured root directory. This prevents clients from using paths such as:

```text
../../some-private-file
```

to access files outside the data directory.

Subdirectories can also be used as part of a filename, provided they remain underneath the configured root directory.

## API

All API endpoints require authentication.

The exact authentication mechanism is implemented by `csv_data_server.authentication.check_auth`. Clients therefore need to provide the credentials expected by that authentication layer.

### `GET /ls`

Lists the files in the configured data directory.

#### Request

```http
GET /ls
```

#### Response

```json
{
  "files": [
    "temperature.csv",
    "humidity.csv",
    "sensor-01.csv"
  ]
}
```

A successful request returns HTTP `200`.

### `POST /add-rows`

Appends one or more rows to a CSV file.

#### Request

```http
POST /add-rows
Content-Type: application/json
```

Example:

```json
{
  "filename": "temperature.csv",
  "headers": ["timestamp", "temperature"],
  "rows": [
    ["2024-01-01T12:00:00Z", 21.4],
    ["2024-01-01T12:01:00Z", 21.5]
  ]
}
```

The `headers` field is optional.

The server creates the file if it does not already exist. If headers are supplied when creating a new file, they are written as the first line.

For an existing file, the headers are not added again.

A successful request returns:

```http
HTTP 200
```

with an empty response body.

### `GET /get-file`

Downloads a CSV file.

#### Request

```http
GET /get-file?filename=temperature.csv
```

The response is returned as a downloadable file with the filename supplied in the request.

For example, using `curl`:

```bash
curl -O -J "http://localhost:5000/get-file?filename=temperature.csv"
```

Authentication must also be supplied according to the server's authentication configuration.

## Example: Temperature Sensor

One intended use of this server is collecting measurements from a small device such as an ESP32.

A sensor can periodically send measurements to `/add-rows`.

For example, a measurement could be represented as:

```json
{
  "filename": "temperature.csv",
  "headers": ["timestamp", "temperature"],
  "rows": [
    ["2024-01-01T12:00:00Z", 21.4]
  ]
}
```

The ESP32 can then repeat this request every time a new measurement is available.

This makes the server a very simple data collection endpoint:

```text
┌──────────────┐
│    ESP32     │
│ Temperature  │
│    Sensor    │
└──────┬───────┘
       │
       │ POST /add-rows
       │
       ▼
┌──────────────────┐
│  CSV Data Server │
│      Flask       │
└────────┬─────────┘
         │
         │
         ▼
   ┌─────────────┐
   │ data/       │
   │ temperature │
   │ .csv        │
   └─────────────┘
```

The resulting CSV file can then be retrieved using `/get-file`.

## Example Client

A simple Python client might look like:

```python
import requests

url = "http://localhost:5000/add-rows"

payload = {
    "filename": "temperature.csv",
    "headers": ["timestamp", "temperature"],
    "rows": [
        ["2024-01-01T12:00:00Z", 21.4]
    ]
}

response = requests.post(
    url,
    json=payload,
    # Supply authentication here
)

response.raise_for_status()
```

Files can subsequently be downloaded with:

```python
import requests

response = requests.get(
    "http://localhost:5000/get-file",
    params={"filename": "temperature.csv"},
    # Supply authentication here
)

response.raise_for_status()

with open("temperature.csv", "wb") as f:
    f.write(response.content)
```

## CSV Format

Rows are currently written using a simple comma-joining approach:

```python
','.join(map(str, row))
```

For example:

```text
timestamp,temperature
2024-01-01T12:00:00Z,21.4
2024-01-01T12:01:00Z,21.5
```

This is intentionally simple, but it means the server does **not currently implement full CSV quoting/escaping**.

In particular, values containing commas, quotes, or newlines may not produce valid CSV.

If arbitrary CSV data needs to be supported, the implementation should use Python's standard-library `csv` module instead.

## Error Handling

The API generally returns HTTP `400 Bad Request` when a request cannot be processed.

Examples include:

* Missing JSON data
* Invalid request data
* Missing `filename`
* Invalid filenames
* Filesystem errors reported by the application

Authentication failures are handled by the authentication module.

## Security Considerations

This server was designed as a small/simple data collection service rather than a general-purpose public-facing file server.

In particular:

* Use a strong password.
* Do not commit `.env` to source control.
* Avoid exposing the server directly to the public internet.
* Consider placing it behind a firewall or VPN.
* Use HTTPS if credentials or sensor data are transmitted over an untrusted network.
* Set `DATA_SERVER_DEBUG=false` outside development.
* The current authentication implementation should be reviewed before deploying the server outside a trusted network.

The application does protect against basic path traversal by ensuring requested files remain underneath `DATA_SERVER_ROOT_DIR`.

## License

This project is distributed under the MIT license. For more information, read `LICENSE`.
