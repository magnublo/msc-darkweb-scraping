import abc
import logging
from enum import Enum
from typing import Callable
from src.utils import get_logger_name


class Severity(Enum):
    CRITICAL = logging.CRITICAL
    FATAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class LoggingWrapper:

    def __init__(self, logger: logging.Logger, custom_message_func: Callable[[str], str]):
        self._logger = logger
        self.get_customized_message = custom_message_func

    def critical(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.critical(custom_msg)

    def fatal(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.fatal(custom_msg)

    def error(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.error(custom_msg)

    def warning(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.warning(custom_msg)

    def warn(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.warn(custom_msg)

    def info(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.info(custom_msg)

    def debug(self, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.debug(custom_msg)

    def log(self, severity: Severity, msg: str):
        custom_msg = self.get_customized_message(msg)
        return self._logger.log(severity, custom_msg)


class MetaBase(abc.ABCMeta):
    def __init__(cls, *args):

        super().__init__(*args)
        base_logger_class_name = "BaseClassWithLogger"
        parent_class_names = [a_class.__name__ for a_class in cls.mro()]
        if base_logger_class_name in parent_class_names and cls.__name__ != base_logger_class_name:
            logger_attribute_name = get_logger_name(cls)
            setattr(cls, logger_attribute_name, logging.getLogger(logger_attribute_name))


class BaseClassWithLogger(metaclass=MetaBase):

    def __init__(self):
        if self.__class__ != BaseClassWithLogger:
            real_logger: logging.Logger = getattr(self, get_logger_name(self.__class__))
            self.logger: LoggingWrapper = LoggingWrapper(real_logger, self._format_logger_message)

    @abc.abstractmethod
    def _format_logger_message(self, message: str) -> str:
        raise NotImplementedError('')
