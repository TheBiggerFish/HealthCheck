

import time
from datetime import datetime
from typing import List, Optional, Tuple

from fishpy.utility import Logger

from services import Service


class Scheduler:
    def __init__(self, services: Optional[List[Service]] = None, logger: Optional[Logger] = None):
        if services is None:
            self.services = []
        else:
            self.services = services
        self._logger = logger

    def register(self, service: Service) -> bool:
        if service.is_valid():
            self.services.append(service)
            if self._logger is not None:
                self._logger.info('Registered %s "%s" in scheduler',
                                  service.__class__.__name__, service.name)
            return True
        if self._logger is not None:
            self._logger.warn('Failed to register %s "%s" in scheduler: '
                              'service configuration not valid',
                              service.__class__.__name__, service.name)
        return False

    @property
    def service_times(self) -> List[Tuple[datetime, Service]]:
        return sorted([(service.get_next_time(), service) for service in self.services])

    def serve(self) -> None:
        if self._logger is not None:
            self._logger.info('Scheduler ready to serve %d services',
                              len(self.services))
        while True:
            if self.services:
                now = datetime.now()
                if self._logger is not None:
                    self._logger.debug('Checking timing for %d services',
                                       len(self.services))
                next_run_times = self.service_times

                if self._logger is not None:
                    self._logger.debug('Calculating sleep time')
                sleep_time = (next_run_times[0][0] - now).total_seconds()
                if self._logger is not None:
                    self._logger.debug('Sleep time for service "%s" is %f seconds',
                                       next_run_times[0][1], sleep_time)

                if self._logger is not None:
                    self._logger.info(
                        'Sleeping for (%.3f) seconds', sleep_time)
                time.sleep(sleep_time)
                if self._logger is not None:
                    self._logger.debug('Woke up from sleep after %.3f seconds',
                                       (datetime.now() - now).total_seconds())
                for run_time, service in next_run_times:
                    if run_time < datetime.now():
                        if self._logger is not None:
                            self._logger.debug('Performing health check on service "%s"',
                                               service)
                        if service.check_health():
                            if self._logger is not None:
                                self._logger.info('Service "%s" is healthy',
                                                  service)
                        elif self._logger is not None:
                            self._logger.log(service.failure_log_level,
                                             'Service "%s" has failed health check',
                                             service)
                    else:
                        if self._logger is not None:
                            self._logger.debug('Skipping health check on service "%s" '
                                               'because it is not yet time', service)
            else:
                if self._logger is not None:
                    self._logger.warn('No services to check, sleeping 1 hour')
                time.sleep(3600)
