# -*- coding: utf-8 -*-
import requests
from requests import Response

from .models import RepecError, RepecJelResult, RepecResultList, RepecSingleResult

BASE_URL = "https://api.repec.org/call.cgi"

# API keywords.
SHORTID = "shortid"
CODE = "code"
ERROR = "error"

# Remote methods.
GET_JEL_FOR_ITEM = "getjelforitem"
GET_AUTHOR_RECORD_FULL = "getauthorrecordfull"
GET_INST_AUTHORS = "getinstauthors"
GET_AUTHORS_FOR_ITEM = "getauthorsforitem"
GET_REF = "getref"


class Repec:
    """
    Wrapper for REPEC API.

    This class provides methods to query upstream API
    services. It implements a basic in-session cache to avoid multiple calls
    for the same query.
    """

    def __init__(self, token: str, **kwargs):
        """
        Initialize a Repec object.

        :param token: string with the authorization token from Repec
        :param kwargs: delegated to `requests.Session`
        """
        self.token = token
        self._session = requests.Session(**kwargs)
        self._cache = {}

    def get_org_authors(self, org_id: str) -> RepecResultList:
        """
        Return the authors beloging to a a given organization.

        param: org_id: Organization ID (as assigned by RePec)
        :return: list of author IDs
        :rtype: an object of :class:`models.RepecResultList`
        """
        data, error = self._request_data(GET_INST_AUTHORS, org_id)

        return RepecResultList(data=data, error=error)

    def get_author_data(self, author_id: str) -> RepecSingleResult:
        """
        Return all data available for a given author.

        :param author_id: Author ID
        :return: Author data
        :rtype: an object of :class:`models.RepecSingleResult`
        """
        data, error = self._request_data(GET_AUTHOR_RECORD_FULL, author_id)

        # Convert to single result.
        data = data[0] if data else {}

        res = RepecSingleResult(data=data, error=error)

        # Fill author id if needed.
        if SHORTID in res.data and res.data[SHORTID] is None:
            res.data[SHORTID] = author_id

        return res

    def get_authors_for_item(self, item_id: str) -> RepecResultList:
        """
        Return the authors of an item (paper or article).

        :param item_id: Item ID for paper or article
        :return: author IDs
        :rtype: an object of :class:`models.RepecResultList`
        """
        data, error = self._request_data(GET_AUTHORS_FOR_ITEM, item_id)

        return RepecResultList(data=data, error=error)

    def get_jel_codes(self, item_id: str) -> RepecJelResult:
        """
        Return the list of JEL codes associated to an item.

        Items can be papers or articles and are identified by an item_id.

        :param item_id: ID of the item
        :return: list of JEL codes
        :rtype: an object of :class:`models.RepecJelResult`
        """
        data, error = self._request_data(GET_JEL_FOR_ITEM, item_id)

        return RepecJelResult(data=data, error=error)

    def get_ref(self, item_id: str) -> RepecSingleResult:
        """
        Return bibliographic references of an item.

        Items can be papers or articles and are identified by an item_id.

        :param item_id: ID of the item
        :return: list of JEL codes
        :rtype: an object of :class:`models.RepecSingleResult`
        """

        data, error = self._request_data(GET_REF, item_id)
        data = data[0] if len(data) else {}

        return RepecSingleResult(data=data, error=error)

    def get_error(self, err_code: int) -> list[str, str]:
        """
        Return the full error description given its numerical code.

        :param err_code: Error code
        :return: Error function and message
        :rtype: an tuple of string
        """
        # Prepare payload for HTTP request.
        payload = {}
        payload[CODE] = self.token
        payload[ERROR] = err_code

        # Send the requests to REPEC API.
        resp = self._session.get(BASE_URL, params=payload)

        # Check for HTTP 4xx-6xx errors.
        resp.raise_for_status()
        json_data = resp.json()

        # Error here should be a wrong token.
        if ERROR in json_data[0]:
            return (
                "N/A",
                "Impossible to get an error information. Probably token is not valid.",
            )

        err_func = json_data[0]["function"]
        err_msg = json_data[0]["description"]

        return err_func, err_msg

    def _request_data(self, api_method: str, query_key: str) -> list[list, RepecError]:
        """
        Request data from RePec API.

        :param api_method: API remote method
        :param query_key: Query key for API
        :return: list of results and an object for remote errors (or None if no
            errors are returned)
        :rtype: tuple with a list of `dicts` and an object of
            :class:`models.RepecResultList`
        """
        # Init cache for this method.
        if api_method not in self._cache:
            self._cache[api_method] = {}

        # Cache hit.
        if query_key in self._cache[api_method]:
            return self._cache[api_method][query_key]

        # Prepare payload for HTTP request.
        payload = {}
        payload[CODE] = self.token
        payload[api_method] = query_key

        # Send the requests to REPEC API.
        resp = self._session.get(BASE_URL, params=payload)

        # Check for HTTP 4xx-6xx errors.
        resp.raise_for_status()

        # Process data received by REPEC API and prepare the final data
        # structure to retun.
        data, error = self._process_data(resp)

        # Cache the result for future calls.
        if not error:
            self._cache[api_method][query_key] = (data, error)

        return data, error

    def _process_data(self, resp: Response) -> list[list, RepecError]:
        """
        Cast HTTP response from Repec to the models.

        :param respo: HTTP response (`requests.Response`)
        :return: list of results and an object for remote errors (or None if no
            errors are returned)
        :rtype: tuple with a list of `dicts` and an object of
            :class:`models.RepecResultList`
        """

        # if we are here but the response il empty, raise an error:
        if len(resp.text.strip()) == 0:
            return [], RepecError(code=404, message="Not found", url=resp.url)

        # Try to JSON-decode the response.
        api_data = resp.json()

        # Check for data: if there's no data just return an empty result
        if not api_data:
            return [], RepecError(url=resp.url)

        # Check for errors raised by REPEC API.
        if ERROR in api_data[0]:
            # Parse the error from response.
            dict_error = api_data[0]
            err_code = dict_error[ERROR]

            # Try to retrieve error function and message.
            err_func, err_msg = self.get_error(err_code)

            # Yields empty data end error object.
            return [], RepecError(
                code=err_code, url=resp.url, function=err_func, message=err_msg
            )

        return api_data, None
