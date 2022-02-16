"""Exceptions to be used in running health check service"""


class HealthCheckException(Exception):
    """Exception to represent issues in the HealthCheck service"""


class ConfigFileException(HealthCheckException):
    """Exception to represent issues loading config in the HealthCheck service"""


class ServiceException(HealthCheckException):
    """Exception to represent issues building/running services in the HealthCheck service"""


class CronException(HealthCheckException):
    """Exception to represent issues interpreting cron expressions in the HealthCheck service"""
