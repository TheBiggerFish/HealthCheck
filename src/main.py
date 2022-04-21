"""
    Written by Cameron Haddock

    This service can be used to run low-priority scheduled health
    checks through HTTP/1 GET requests. The results are logged to
    stdout or SysLog by configuration in .env file.
"""

import os
import time
from typing import Any, Dict, List, Optional, Type

import dotenv
import yaml
from fishpy.utility import Logger
from fishpy.utility.network import online

from exceptions import ConfigFileException
from scheduler import Scheduler
from services import service_mapping
from src.exceptions import ServiceException
from src.services.service import Service

dotenv.load_dotenv()
CONFIG_PATH = os.getenv('CONFIG_PATH')
LOGGING_NAME = os.getenv('LOGGING_NAME')
LOGGING_HOST = os.getenv('LOGGING_HOST')
LOGGING_PORT = os.getenv('LOGGING_PORT', 514)
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
logger = Logger(LOGGING_NAME, LOGGING_LEVEL,
                LOGGING_HOST, LOGGING_PORT)
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
    # TODO: switch to a service registration system which allows different types of services
    while not online(logger):
        logger.error('Failed to connect, waiting 60 seconds')
        time.sleep(60)

    config = load_config()
    services: dict[str, dict[str, Any]] = config['services']
    scheduler = Scheduler(logger=logger)

    for service_name, service_config in services.items():
        service_type: Optional[str] = service_config.get('type')
        if service_type is None:
            logger.warning('Skipping service "%s" due to missing service type',
                           service_name)
            continue

        service_class: Type[Service] = service_mapping.get(service_type)
        if service_class is None:
            logger.warning('Skipping service "%s" due to unknown service type',
                           service_name)
            continue

        service = service_class(service_name, service_config, logger=logger)

        logger.debug('Attempting to register service "%s"', service)
        registered = scheduler.register(service)

        if not registered:
            logger.warning('Skipping service "%s" due to invalid config',
                           service_name)

    scheduler.serve()


if __name__ == '__main__':
    main()
