"""
    Written by Cameron Haddock

    This service can be used to run low-priority scheduled health
    checks through HTTP/1 GET requests. The results are logged to
    stdout or SysLog by configuration in .env file.
"""

import os
from logging import _nameToLevel
from typing import Dict

import dotenv
import requests
import yaml
from fishpy.logger import Logger
from py_cron_schedule import CronFormatError, CronSchedule

dotenv.load_dotenv()
CONFIG_PATH = os.getenv('CONFIG_PATH')
LOGGING_HOST = os.getenv('LOGGING_HOST')
LOGGING_PORT = os.getenv('LOGGING_PORT')
LOGGING_NAME = os.getenv('LOGGING_NAME')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL')
logger = Logger(LOGGING_NAME,LOGGING_HOST,
                LOGGING_PORT,LOGGING_LEVEL)
logger.debug('Logger configured: {{"name":%s,"level":%s,"host":%s,"port":%s}}',
             LOGGING_HOST,LOGGING_LEVEL,LOGGING_HOST,LOGGING_PORT)


def load_config() -> Dict:
    """Load the service configuration from config.yml file"""

    try:
        # Try to access config.yml for service health check configurations
        logger.debug('Opening configuration file: %s', CONFIG_PATH)
        if CONFIG_PATH is None:
            logger.fatal('CONFIG_PATH environment variable not defined')
        with open(CONFIG_PATH,encoding='UTF-8') as config_file:
            config = yaml.safe_load(config_file)
    except IOError as err:
        logger.fatal('Error opening configuration file: %s', str(err))

    return config


def is_online(service, check_config) -> bool:
    """Check if a service is online by sending a health check request"""

    logger.debug('Checking status of service {%s}',service)

    # Determine the integer log level to use for this service in case of failure
    failure_level = _nameToLevel[check_config['failure_log_level']]

    # Perform the health check HTTP GET request
    response = requests.get(check_config['url'])

    # Logging template function for health check failures
    log_health_failure = lambda reason, *args: \
        logger.log(failure_level,'Health check failed for service {%s},' + reason, service, *args)

    # If expected responses have been configured in config.yml for this service
    if 'expected_response' in check_config:
        expected = check_config['expected_response']

        # If expected response status code has been configured in config.yml for this service
        if 'code' in expected:
            logger.debug('Checking expected_response code of service {%s}', service)

            # Fail health check if received status code does not match configured
            if response.status_code != expected['code']:
                log_health_failure('received unexpected status code {%d}',response.status_code)
                return False

        # If expected response body has been configured in config.yml for this service
        if 'body' in expected:
            logger.debug('Checking expected_response body of service {%s}', service)

            # Fail health check if received body does not match configured
            if response.text != expected['body']:
                log_health_failure('received unexpected response body "%s"',response.text)
                return False

        # If expected response JSON property has been configured in config.yml for this service
        if 'json_property' in expected:
            logger.debug('Checking expected_response json_property of service {%s}', service)

            # Logging template function for expected json_property failures
            log_key_error = lambda key: \
                log_health_failure('unable to access json_property using provided key {%s}',key)

            json = response.json()

            # Traverse JSON object to reach expected value
            for key in expected['json_property']['keys']:

                # Fail health check if JSON object does not match expected format
                if not isinstance(json,(dict,list)):
                    log_key_error(key)
                    return False

                if isinstance(json,list):
                    # Fail health check if trying to use string as a key in a list access
                    if isinstance(key,str):
                        log_key_error(key)
                        return False

                    # Fail health check if integer key out of range of list
                    if isinstance(key,int) and not 0 <= key < len(json):
                        log_key_error(key)
                        return False

                # Fail health check if key not in JSON object dictionary (object not traversable)
                elif key not in json:
                    log_key_error(key)
                    return False

                # Update JSON object to continue traversal
                json = json[key]

            # Fail health check if found JSON property does not match expected value
            if json != expected['json_property']['value']:
                log_health_failure('received unexpected json_property value {%s}',str(json))
                return False

    # If no expected responses have been configured in config.yml, default to status_code == 200
    if response.status_code != 200:
        log_health_failure('received unexpected status code {%d}',response.status_code)
        return False

    # If not returned false elsewhere, health check must have succeeded
    logger.info('Health check passed for service {%s}',service)
    return True


def main() -> None:
    """Main function of health check script"""

    config = load_config()
    scheduler = CronSchedule()

    # Add default debug task to validate that health checker is running
    scheduler.add_task('Scheduler','* * * * *',logger.debug,
                       'Health check scheduler is running')


    service_count = len(config['services'])

    # Service configuration and scheduling loop
    for service in config['services']:

        # Cron string to schedule service
        cron:str = config['services'][service]['cron']

        # Health check configuration
        check_config = config['services'][service]['healthcheck']

        # Arguments to be passed to is_online function
        args = (service, check_config)

        try:
            # Add service health check task to scheduler
            scheduler.add_task(service, cron, is_online, *args)
            logger.debug('Service {%s} added to scheduler on schedule "%s" with configuration:\n%s',
                         service,cron,str(check_config))
        except CronFormatError:
            logger.error('Failed to interpet cron "%s" for service {%s}',
                         cron, service)
            service_count -= 1

    logger.info('Started health checker on (%d) services', service_count)
    try:
        # Start scheduler, check schedule every {min_schedule_ms} milliseconds
        scheduler.start(min_schedule_ms=500)
    except KeyboardInterrupt:
        logger.info('Stopping health checker with keyboard interrupt')


if __name__ == '__main__':
    main()
