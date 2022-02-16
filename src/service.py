"""Class used to reprsent services to be health-checked"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from croniter import croniter
from fishpy.utility.logging import NAME_TO_LEVEL


class Service:
    """Class used to reprsent services to be health-checked"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.cron_expression: str = '0 * * * *'
        self.url: Optional[str] = None
        self.failure_log_level_name: str = 'ERROR'
        self.failure_log_level: int = 40
        self.response_code: int = 200
        self.match_body: Optional[str] = None
        self.match_json_path: List[Union[str, int]] = []
        self._read_config(config)
        self.schedule = croniter(self.cron_expression, datetime.now())

    def _read_config(self, config: Dict[str, Any]):
        self.cron_expression = config.get('cron', '0 * * * *')
        self.url = config.get('url')

        self.failure_log_level_name = config.get(
            'failure_log_level', 'ERROR').upper()
        self.failure_log_level = NAME_TO_LEVEL.get(self.failure_log_level_name)

        self.response_code = config.get('code', 200)
        self.match_body = config.get('body')

        json_body: Optional[Dict[str, Any]] = config.get('json_body')
        if json_body is not None:
            self.match_body = json_body.get('value')
            self.match_json_path = json_body.get('keys', [])

    def check_health(self) -> bool:
        """Perform a health check, returning up status"""

        try:
            resp = requests.get(self.url)
        except requests.exceptions.ConnectionError:
            return False
        body = resp.text

        if self.match_body is not None:
            if self.match_json_path:
                json = resp.json()
                for level in self.match_json_path:
                    json = json[level]
                body = str(json)
            if body == self.match_body:
                return True

        return self.response_code == resp.status_code

    def is_valid(self) -> bool:
        """Returns true if the Service is valid"""
        return self.url is not None

    def get_next_time(self) -> datetime:
        cur = self.schedule.get_current(datetime)
        if cur < datetime.now():
            return self.schedule.next(datetime)
        return cur

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(name=\'{self.name}\','
                f'expression=\'{self.cron_expression}\','
                f'url=\'{self.url}\')')
