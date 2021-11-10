# HealthCheck

This service can be used to run low-priority scheduled health checks through HTTP/1 GET requests. The results are logged to stdout or SysLog

## Setup to Use Existing Infrastructure

Create pull request to add your server configuration to config.yml

## Setup to Self-Host

Written for `Python 3.8.10` 

`pip install .`

---
Create *.env* file in directory with following parameters

* `CONFIG_PATH`* (path to config.yml)
* `LOGGING_NAME`* (name of service displayed in log output)
* `LOGGING_HOST` (host of log aggregator, e.g. localhost)
* `LOGGING_PORT` (port of log aggregator, e.g. 514)
* `LOGGING_LEVEL` (log output threshold, e.g. DEBUG,INFO,WARNING)

If `LOGGING_HOST` not provided, logs output to stdout \
**required*

---
Add line to crontab for auto-run on startup \
```@reboot sudo /usr/local/bin/python3 /path/to/check.py &```

---
Create server configurations in config.yml
