
import abc
from datetime import datetime
from typing import Optional

from croniter import croniter
from fishpy.utility.logging import NAME_TO_LEVEL, Logger


class Service(abc.ABC):
    """Class used to represent services to be health-checked"""

    def __init__(self, name: str, cron_expr: str = '0 * * * *',
                 fail_log_level: str = 'ERROR',
                 logger: Optional[Logger] = None):
        self.name = name
        self.cron_expression: str = cron_expr
        self.failure_log_level_name: str = fail_log_level
        self.failure_log_level: int = NAME_TO_LEVEL[fail_log_level]
        self.schedule = croniter(self.cron_expression, datetime.now())
        self._logger = logger

    def get_next_time(self) -> datetime:
        cur: datetime = self.schedule.get_current(datetime)
        if cur < datetime.now():
            next_: datetime = self.schedule.next(datetime)
            if self._logger is not None:
                self._logger.debug('Updated next scheduled time for %s "%s" to (%s)',
                                   self.__class__.__name__, self.name,
                                   next_.strftime('%Y-%m-%d %H:%M:%S'))
            return next_
        return cur

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(name=\'{self.name}\','
                f'expression=\'{self.cron_expression}\'')

    def __lt__(self, other: 'Service') -> bool:
        return self.name < other.name

    @abc.abstractclassmethod
    def is_valid(self) -> bool:
        """Returns true if the Service is valid"""
        pass

    @abc.abstractclassmethod
    def check_health(self) -> bool:
        """Perform a health check, returning up status"""
        pass
