# -*- coding: utf-8 -*-
import html
import re
from typing import Optional

import requests
from requests import Response

from .models import RepecError, RepecJelResult, RepecResultList, RepecSingleResult

BASE_URL = "https://api.repec.org/call.cgi"
ERROR_LOOKUP_URL = "https://ideas.repec.org/cgi-bin/getapierror.cgi"

# API keywords.
SHORTID = "shortid"
CODE = "code"
ERROR = "error"
NUMBER = "number"

ERROR_LOOKUP_PATTERN = re.compile(
    r"Error\s+\d+\s+applies\s+to\s+function\s+"
    r"<b[^>]*>(?P<function>.*?)</b>\s*:\s*"
    r"(?P<description>.*?)(?=<p\b|</div>|$)",
    re.IGNORECASE | re.DOTALL,
)

# Remote methods.
GET_JEL_FOR_ITEM = "getjelforitem"
GET_AUTHOR_RECORD_FULL = "getauthorrecordfull"
GET_INST_AUTHORS = "getinstauthors"
GET_AUTHORS_FOR_ITEM = "getauthorsforitem"
GET_REF = "getref"


class Repec:
    """Client for the RePEc API.

    The client provides methods for querying upstream RePEc services. Successful
    requests are cached for the lifetime of the client to avoid repeated calls
    for the same method and identifier.
    """

    def __init__(self, token: str, **kwargs):
        """
        Initialize a RePEc API client.

        :param token: Authorization token issued by RePEc.
        :param kwargs: Keyword arguments passed to :class:`requests.Session`.
        """
        self.token = token
        self._session = requests.Session(**kwargs)
        self._cache = {}

    def get_org_authors(self, org_id: str) -> RepecResultList:
        """
        Return the authors belonging to an organization.

        :param org_id: Organization identifier assigned by RePEc.
        :return: Result containing the matching author records or a RePEc error.
        :rtype: RepecResultList
        """
        data, error = self._request_data(GET_INST_AUTHORS, org_id)

        return RepecResultList(data=data, error=error)

    def get_author_data(self, author_id: str) -> RepecSingleResult:
        """
        Return all available data for an author.

        :param author_id: RePEc author identifier.
        :return: Result containing the author record or a RePEc error.
        :rtype: RepecSingleResult
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
        Return the authors of a paper or article.

        :param item_id: RePEc identifier for the paper or article.
        :return: Result containing the matching author records or a RePEc error.
        :rtype: RepecResultList
        """
        data, error = self._request_data(GET_AUTHORS_FOR_ITEM, item_id)

        return RepecResultList(data=data, error=error)

    def get_jel_codes(self, item_id: str) -> RepecJelResult:
        """
        Return the JEL codes associated with a paper or article.

        :param item_id: RePEc identifier for the paper or article.
        :return: Result containing the matching JEL codes or a RePEc error.
        :rtype: RepecJelResult
        """
        data, error = self._request_data(GET_JEL_FOR_ITEM, item_id)

        return RepecJelResult(data=data, error=error)

    def get_ref(self, item_id: str) -> RepecSingleResult:
        """
        Return the bibliographic references of a paper or article.

        :param item_id: RePEc identifier for the paper or article.
        :return: Result containing bibliographic reference data or a RePEc error.
        :rtype: RepecSingleResult
        """

        data, error = self._request_data(GET_REF, item_id)
        data = data[0] if len(data) else {}

        return RepecSingleResult(data=data, error=error)

    def get_error(self, err_code: int) -> tuple[str, str]:
        """
        Return the description associated with a numerical RePEc error code.

        :param err_code: Numerical error code returned by RePEc.
        :return: Pair containing the originating function and error description.
        :rtype: tuple[str, str]
        """
        payload = {CODE: self.token, NUMBER: err_code}

        resp = self._session.get(ERROR_LOOKUP_URL, params=payload)

        resp.raise_for_status()

        match = ERROR_LOOKUP_PATTERN.search(resp.text)
        if match is None:
            return "N/A", "Impossible to get error information from RePEc."

        err_func = html.unescape(match.group("function")).strip()
        err_msg = html.unescape(match.group("description")).strip()

        return err_func, err_msg

    def _request_data(
        self, api_method: str, query_key: str
    ) -> tuple[list, Optional[RepecError]]:
        """
        Request data from a RePEc API method.

        :param api_method: Name of the remote API method.
        :param query_key: Identifier passed to the remote method.
        :return: Pair containing response items and an optional RePEc error.
        :rtype: tuple[list, Optional[RepecError]]
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
        # structure to return.
        data, error = self._process_data(resp)

        # Cache the result for future calls.
        if not error:
            self._cache[api_method][query_key] = (data, error)

        return data, error

    def _process_data(self, resp: Response) -> tuple[list, Optional[RepecError]]:
        """
        Convert an HTTP response into data and an optional RePEc error.

        :param resp: Response returned by :class:`requests.Session`.
        :return: Pair containing decoded response items and an optional error.
        :rtype: tuple[list, Optional[RepecError]]
        """

        # If the response is empty, return an error.
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
