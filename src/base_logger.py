import abc
import logging

from logger_config import get_logger_name


class MetaBase(abc.ABCMeta):
    def __init__(cls, *args):

        super().__init__(*args)
        base_logger_class_name = "BaseClassWithLogger"
        parent_class_names = [aclass.__name__ for aclass in cls.mro()]
        if base_logger_class_name in parent_class_names and cls.__name__ != base_logger_class_name:
            logger_attribute_name = get_logger_name(cls)
            setattr(cls, logger_attribute_name, logging.getLogger(logger_attribute_name))


class BaseClassWithLogger(metaclass=MetaBase):

    def __init__(self):
        if self.__class__ != BaseClassWithLogger:
            self.logger: logging.Logger = getattr(self, get_logger_name(self.__class__))
