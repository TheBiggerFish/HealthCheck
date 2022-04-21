"""Class used to reprsent services to be health-checked"""

from typing import Any, Dict, List, Optional, Union

import requests
from fishpy.utility.logging import Logger

from .service import Service


class HttpService(Service):
    """Class used to represent services to be health-checked"""

    def __init__(self, name: str, config: Dict[str, Any], logger: Optional[Logger] = None):
        cron_expression: str = config.get('cron', '0 * * * *')
        failure_log_level_name: str = config.get('failure_log_level', 'ERROR'
                                                 ).upper()
        super().__init__(name, cron_expression, failure_log_level_name, logger)

        self.url: Optional[str] = config.get('url')
        self.response_code: int = config.get('code', 200)

        self.match_body: Optional[str] = config.get('body')

        json_body: Optional[Dict[str, Any]] = config.get('json_body')
        if json_body is not None:
            self.match_body = json_body.get('value')
            self.match_json_path: List[Union[str, int]] = \
                json_body.get('keys', [])

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(name=\'{self.name}\','
                f'expression=\'{self.cron_expression}\','
                f'url=\'{self.url}\')')

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
