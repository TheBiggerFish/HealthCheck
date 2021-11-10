"""DOCSTRING"""

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
        logger.debug('Opening configuration file: %s', CONFIG_PATH)
        if CONFIG_PATH is None:
            logger.fatal('CONFIG_PATH environment variable not defined')
        with open(CONFIG_PATH,encoding='UTF-8') as config_file:
            config = yaml.safe_load(config_file)
    except IOError as err:
        logger.fatal('Error opening configuration file: %s', str(err))
    return config


def is_online(service, check_data) -> bool:
    """Check if a service is online by sending a health check request"""

    logger.debug('Checking status of service {%s}',service)
    failure_level = _nameToLevel[check_data['failure_log_level']]

    response = requests.get(check_data['url'])

    if 'response' in check_data:
        if 'expected_code' in check_data['response'] and \
                response.status_code != check_data['response']['expected_code']:
            logger.log(failure_level,'Health-check failed for service {%s}, '\
                'received unexpected status code {%d}',
                service, response.status_code)
            return False

        if 'body' in check_data['response'] and \
                response.text != check_data['response']['body']:
            logger.log(failure_level,'Health-check failed for service {%s}, '\
                'received unexpected response body {%d}',
                service, response.text)
            return False

        if response.status_code != 200:
            logger.log(failure_level,'Health-check failed for service {%s}, '\
                'received unexpected status code {%d}',
                service, response.status_code)
            return False

    elif response.status_code != 200:
        logger.log(failure_level,'Health-check failed for service {%s}, '\
            'received unexpected status code {%d}',
            service, response.status_code)
        return False

    logger.debug('Health-check passed for service {%s}',service)
    return True


def main() -> None:
    """Main function of health check script"""

    config = load_config()
    scheduler = CronSchedule()
    scheduler.add_task('Scheduler','0 * * * *',logger.debug,
                       'Health-check scheduler is running')

    service_count = len(config['services'])
    for service in config['services']:
        cron:str = config['services'][service]['cron']
        check_data = config['services'][service]['healthcheck']
        args = (service, check_data)

        try:
            scheduler.add_task(service, cron, is_online, *args)
            logger.debug('Service {%s} added to scheduler on schedule "%s" with configuration:\n%s',
                         service,cron,str(check_data))
        except CronFormatError:
            logger.error('Failed to interpet cron "%s" for service {%s}',
                         cron, service)
            service_count -= 1

    logger.info('Started health-checker on (%d) services', service_count)
    try:
        scheduler.start(min_schedule_ms=5000)
    except KeyboardInterrupt:
        logger.info('Stopping health-checker with keyboard interrupt')


if __name__ == '__main__':
    main()
