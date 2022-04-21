# HealthCheck

This service can be used to run low-priority scheduled health checks through HTTP/1 GET requests. The results are logged to stdout or SysLog by configuration in .env file.

## Setup to Use Existing Infrastructure

Create pull request to add your server configuration to config.yml

## Setup to Self-Host

Written for `Python 3.8.10` 

`pip install .`

---
Create *.env* file in directory with following parameters

* `CONFIG_PATH`* (path to config.yml)
* `LOGGING_NAME`* (name of service displayed in log output)
* `LOGGING_HOST` (host of log aggregator, e.g. localhost or 192.168.1.10)
* `LOGGING_PORT` (port of log aggregator, default 514)
* `LOGGING_LEVEL` (log output threshold, e.g. DEBUG,INFO,WARNING, default INFO)

If `LOGGING_HOST` not provided, logs output to stdout \
**required environment variable*

---
Add line to crontab for auto-run on startup \
```@reboot sudo /usr/local/bin/python3 /path/to/main.py &```

Define `$HOSTNAME` as an environment variable representing the local hostname to be logged

---
Create server configurations in config.yml

```
Service_Name:
  type: string    # Type of health check to perform (http | minecraft)
  cron: string    # Health-check schedule in cron syntax (default: '0 * * * *')
  url: string     # URL to direct health checks to
  response:
    # Use only one expected response type
    # Default expected response type is `code: 200`
    code: int
    body: string    # HTTP response text body
    json_body:
      value: any    # Expected value of provided JSON field in HTTP response
      keys:
        # List of JSON keys to access expected JSON field and compare value
        (e.g. json['status']['online'] == value)
      - key1
      - key2
  alert:
    email: string   # Email address of user to alert in event of health check failure
```