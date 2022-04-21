
from typing import Any, Dict, List, Optional, Union

from fishpy.utility import Logger
from mcstatus import MinecraftServer

from .service import Service


class MinecraftService(Service):
    def __init__(self, name: str, config: Dict[str, Any], logger: Optional[Logger] = None):
        cron_expression: str = config.get('cron', '0 * * * *')
        failure_log_level_name: str = config.get('failure_log_level', 'ERROR'
                                                 ).upper()
        super().__init__(name, cron_expression, failure_log_level_name, logger)

        self.ip: Optional[str] = config.get('ip')
        self.port: int = config.get('port', 25565)
        self.server: Optional[MinecraftServer] = None
        if self.ip is not None:
            self.server = MinecraftServer(self.ip, self.port)

    def check_health(self) -> bool:
        try:
            self.server.ping()
        except IOError as err:
            return False
        return True

    def is_valid(self) -> bool:
        """Returns true if the Service is valid"""
        return self.ip is not None
