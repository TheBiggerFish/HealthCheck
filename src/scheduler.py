

import time
from datetime import datetime
from typing import List, Tuple

from fishpy.utility import Logger

from service import Service


class Scheduler:
    def __init__(self, services: List[Service]):
        self.services = services

    @property
    def service_times(self) -> List[Tuple[datetime, Service]]:
        return sorted([(service.get_next_time(), service) for service in self.services])

    def serve(self, logger: Logger) -> None:
        while True:
            if self.services:
                now = datetime.now()
                logger.debug('Checking timing for %d services',
                             len(self.services))
                next_run_times = self.service_times

                logger.debug('Calculating sleep time')
                sleep_time = (next_run_times[0][0] - now).total_seconds()
                logger.debug('Sleep time for service "%s" is %f seconds',
                             next_run_times[0][1], sleep_time)

                logger.info('Sleeping for (%.3f) seconds', sleep_time)
                time.sleep(sleep_time)
                logger.debug('Woke up from sleep after %.3f seconds',
                             (datetime.now() - now).total_seconds())
                for run_time, service in next_run_times:
                    if run_time < datetime.now():
                        logger.debug('Performing health check on service "%s"',
                                     service)
                        if service.check_health():
                            logger.info('Service "%s" is healthy', service)
                        else:
                            logger.log(service.failure_log_level,
                                       'Service "%s" has failed health check',
                                       service)
                    else:
                        logger.debug('Skipping health check on service "%s" '
                                     'because it is not yet time', service)
            else:
                logger.warn('No services to check, sleeping 1 hour')
                time.sleep(3600)
