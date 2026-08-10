# -*- coding: utf-8 -*-

"""Result and error models returned by the PyRepec client."""

from typing import List, Optional, Union

from pydantic import BaseModel


class RepecError(BaseModel):
    """Error returned by a RePEc API service.

    :param code: Numerical RePEc error code, when available.
    :type code: int or None
    :param message: Human-readable description of the error.
    :type message: str
    :param function: RePEc function that originated the error.
    :type function: str
    :param url: Full URL of the RePEc API request.
    :type url: str or None
    """

    code: Union[int, None] = None
    message: Optional[str] = "Unknown Exception"
    function: Optional[str] = "N/A"
    url: Optional[str] = None


class RepecResultList(BaseModel):
    """Result containing a list of RePEc records.

    :param data: Records returned by the API, or an empty list on error.
    :type data: List of dicts
    :param error: RePEc error, or ``None`` when the request succeeds.
    :type error: RepecError or None
    """

    data: List[dict]
    error: Union[Optional[RepecError], None]


class RepecSingleResult(BaseModel):
    """Result containing a single RePEc record.

    :param data: Record returned by the API, or an empty dictionary on error.
    :type data: dict
    :param error: RePEc error, or ``None`` when the request succeeds.
    :type error: RepecError or None
    """

    data: dict
    error: Union[Optional[RepecError], None]


class RepecJelResult(BaseModel):
    """Result containing JEL codes returned by RePEc.

    :param data: JEL codes returned by the API, or an empty list on error.
    :type data: List of str
    :param error: RePEc error, or ``None`` when the request succeeds.
    :type error: RepecError or None
    """

    data: list[str]
    error: Union[Optional[RepecError], None]
