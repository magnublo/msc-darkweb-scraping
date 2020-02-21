from urllib3.exceptions import HTTPError


class DeadMirrorException(Exception):

    def __init__(self):
        super().__init__("Dead mirror, throwing exception and restarting scrape of queue item.")


class LoggedOutException(Exception):
    DEFAULT_TEXT = "Cookie appears to have been invalidated by remote website."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class CustomServerErrorException(HTTPError):
    DEFAULT_TEXT = "Custom server error with 200 status code"

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class EmptyResponseException(HTTPError):
    DEFAULT_TEXT = "200 response has no content."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class BadGatewayException(HTTPError):
    DEFAULT_TEXT = "Received response code 502."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class BadRequestException(HTTPError):
    DEFAULT_TEXT = "Received response code 400."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class InternalServerErrorException(HTTPError):
    DEFAULT_TEXT = "Received response code 500."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class GatewayTimeoutException(HTTPError):
    DEFAULT_TEXT = "Received response code 504."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class GenericException(BaseException):
    DEFAULT_TEXT = "Generic exception."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)


class ServiceUnavailableException(HTTPError):
    DEFAULT_TEXT = "Received response code 500."

    def __init__(self, text=DEFAULT_TEXT):
        super().__init__(text)
