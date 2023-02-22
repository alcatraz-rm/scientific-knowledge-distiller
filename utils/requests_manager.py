import time

import requests


def catch_network_errors(method):
    """
    Decorator for network errors catching.
    """

    def inner(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except (
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException,
                Exception,
        ) as network_error:
            return network_error

    return inner


@catch_network_errors
def _get(session, *args, **kwargs):
    """
    Make safe GET response using given session and arguments.
    :param session: session for response making
    :type session: requests.Session
    :return: response if success, else catch error
    :rtype: Union[requests.Response, Exception]
    """

    return session.get(*args, **kwargs)


@catch_network_errors
def _post(session, *args, **kwargs):
    """
    Make safe POST response using given session and arguments.
    :param session: session for response making
    :type session: requests.Session
    :return: response if success, else catch error
    :rtype: Union[requests.Response, Exception]
    """

    return session.post(*args, **kwargs)


class RequestsManager:
    def __init__(self):
        self._session = requests.Session()

    def get(self, *args, **kwargs):
        max_failures = kwargs.get('max_failures', 10)
        kwargs.pop('max_failures')

        while max_failures >= 0:
            result = _get(self._session, *args, **kwargs)

            if isinstance(result, requests.Response) and (result.status_code == 200 or max_failures == 0):
                return result

            max_failures -= 1
            time.sleep(5)

    def post(self, *args, **kwargs):
        max_failures = kwargs.get('max_failures', 10)
        kwargs.pop('max_failures')

        while max_failures >= 0:
            result = _post(self._session, *args, **kwargs)

            if isinstance(result, requests.Response) and (result.status_code == 200 or max_failures == 0):
                return result

            max_failures -= 1
            time.sleep(15)
