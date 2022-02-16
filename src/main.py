"""
    Written by Cameron Haddock

    This service can be used to run low-priority scheduled health
    checks through HTTP/1 GET requests. The results are logged to
    stdout or SysLog by configuration in .env file.
"""

import os
import time
from typing import Dict, List

import dotenv
import yaml
from fishpy.utility import Logger
from fishpy.utility.network import online

from exceptions import ConfigFileException
from scheduler import Scheduler
from service import Service

dotenv.load_dotenv()
CONFIG_PATH = os.getenv('CONFIG_PATH')
LOGGING_HOST = os.getenv('LOGGING_HOST')
LOGGING_PORT = os.getenv('LOGGING_PORT')
LOGGING_NAME = os.getenv('LOGGING_NAME')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL')
logger = Logger(LOGGING_NAME, LOGGING_HOST,
                LOGGING_PORT, LOGGING_LEVEL)
logger.debug('Logger configured: {{"name":%s,"level":%s,"host":%s,"port":%s}}',
             LOGGING_HOST, LOGGING_LEVEL, LOGGING_HOST, LOGGING_PORT)


def load_config() -> Dict:
    """Load the service configuration from config.yml file"""

    try:
        # Try to access config.yml for service health check configurations
        logger.debug('Opening configuration file: %s', CONFIG_PATH)
        if CONFIG_PATH is None:
            logger.fatal('CONFIG_PATH environment variable not defined')
            raise ConfigFileException(
                'CONFIG_PATH environment variable not defined')
        with open(CONFIG_PATH, encoding='UTF-8') as config_file:
            logger.debug('Successfully opened configuration file')
            config = yaml.safe_load(config_file)
            logger.debug('Successfully loaded configuration file')
    except IOError as err:
        logger.fatal('Error opening configuration file: %s', str(err))
        raise ConfigFileException(
            f'Error opening configuration file: {str(err)}')

    return config


def main():
    while not online(logger):
        logger.error('Failed to connect, waiting 60 seconds')
        time.sleep(60)

    config = load_config()
    services: List[Service] = []
    for service_name in config['services']:
        service = Service(service_name, config['services'][service_name])
        logger.debug('Checking that service "%s" has a url provided', service)
        if service.is_valid():
            logger.info('Adding service "%s" to serve-list with url "%s" on cron schedule (%s), logging at level %s on failure',
                        service, service.url, service.cron_expression, service.failure_log_level_name)
            services.append(service)
        else:
            logger.warning('Skipping service "%s" due to lack of url', service)
    logger.info('Ready to serve %d services', len(services))

    scheduler = Scheduler(services)
    scheduler.serve(logger)


if __name__ == '__main__':
    main()
