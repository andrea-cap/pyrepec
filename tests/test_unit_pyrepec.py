# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

import pytest

from pyrepec import Repec
from pyrepec.models import (
    RepecError,
    RepecJelResult,
    RepecResultList,
    RepecSingleResult,
)
from pyrepec.repec import (
    ERROR_LOOKUP_URL,
    GET_AUTHOR_RECORD_FULL,
    GET_AUTHORS_FOR_ITEM,
    GET_INST_AUTHORS,
    GET_JEL_FOR_ITEM,
    GET_REF,
)


class HttpException(Exception):
    """Mocking HTTP Errors."""


class MockResponse:
    """Mock a requests.Response."""

    def __init__(self, url, json_data, should_fail=False, text=None):
        self.url = url
        self.json_data = json_data
        self.text = json.dumps(json_data) if not text else text
        self.should_fail = should_fail

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.should_fail:
            raise HttpException("Argh!")


def mocked_http_error_request(*args, **kwargs):
    return MockResponse(args[0], [], should_fail=True)


def mocked_empty_requests(*args, **kwargs):
    return MockResponse(args[0], [])


def mocked_empty_test(*args, **kwargs):
    return MockResponse(args[0], [], text="")


def mocked_requests(*args, **kwargs):
    params = kwargs["params"]
    url = args[0]

    if GET_INST_AUTHORS in params:
        handle = params[GET_INST_AUTHORS]
        if handle == "RePEc:edi:bdigvit":
            return MockResponse(url, [{"key": "value"}])

    if GET_AUTHOR_RECORD_FULL in params:
        shortid = params[GET_AUTHOR_RECORD_FULL]
        if shortid == "someauthorid":
            return MockResponse(url, [{"key": "value"}])

    if GET_AUTHORS_FOR_ITEM in params:
        handle = params[GET_AUTHORS_FOR_ITEM]
        if handle == "someitemid":
            return MockResponse(url, [{"key": "value"}])

    if GET_JEL_FOR_ITEM in params:
        handle = params[GET_JEL_FOR_ITEM]
        if handle == "someitemid":
            return MockResponse(url, ["jel1", "jel2"])

    if GET_REF in params:
        handle = params[GET_REF]
        if handle == "someitemid":
            return MockResponse(url, [{"key": "value"}])

    return MockResponse(url, [{"error": "2"}])


@patch("requests.Session.get", side_effect=mocked_requests)
def test_org_authors(mck) -> None:
    """Testing method for authors in organization."""
    repec = Repec("somecode")

    org_id = "RePEc:edi:bdigvit"
    res = repec.get_org_authors(org_id)

    assert isinstance(res, RepecResultList)
    assert res.error is None
    assert len(res.data)

    # No authors found here so we expect a RepecError.
    item_id = "RePEc:dummy"
    res = repec.get_org_authors(item_id)
    assert isinstance(res, RepecResultList)
    assert isinstance(res.error, RepecError)
    assert len(res.data) == 0


@patch("requests.Session.get", side_effect=mocked_http_error_request)
def test_org_authors_http_error(mock_requests) -> None:
    """HTTP errors gets forwared"""
    repec = Repec("somecode")
    # No authors found here so we expect a RepecError.
    item_id = "RePEc:dummy"
    with pytest.raises(HttpException):
        repec.get_org_authors(item_id)


@patch("requests.Session.get", side_effect=mocked_empty_requests)
def test_org_authors_error_with_empty_response(mck) -> None:
    repec = Repec("somecode")
    # No authors found here so we expect a RepecError.
    item_id = "RePEc:dummy"
    res = repec.get_org_authors(item_id)
    assert isinstance(res, RepecResultList)
    assert isinstance(res.error, RepecError)
    assert len(res.data) == 0


@patch("requests.Session.get", side_effect=mocked_requests)
def test_author_data(mck) -> None:
    repec = Repec("somecode")
    author_id = "someauthorid"
    res = repec.get_author_data(author_id)
    assert isinstance(res, RepecSingleResult)
    assert res.error is None
    assert res.data is not None

    item_id = "RePEc:dummy"
    res = repec.get_author_data(item_id)
    assert isinstance(res, RepecSingleResult)
    assert isinstance(res.error, RepecError)
    assert len(res.data) == 0


@patch("requests.Session.get", side_effect=mocked_requests)
def test_author_for_item(mck) -> None:
    """Testing method for item authors."""
    item_id = "someitemid"
    repec = Repec("somecode")
    res = repec.get_authors_for_item(item_id)
    assert isinstance(res, RepecResultList)
    assert res.error is None
    assert len(res.data)

    # No authors found here so we expect a RepecError.
    item_id = "RePEc:dummy"
    res = repec.get_authors_for_item(item_id)
    assert isinstance(res, RepecResultList)
    assert isinstance(res.error, RepecError)
    assert len(res.data) == 0


@patch("requests.Session.get", side_effect=mocked_requests)
def test_jel_codes(mck) -> None:
    """Testing method for JEL codes."""
    item_id = "someitemid"
    repec = Repec("somecode")
    res = repec.get_jel_codes(item_id)
    assert isinstance(res, RepecJelResult)
    assert res.error is None
    assert len(res.data)

    # No JEL codes found here, we expect a RepecError.
    item_id = "RePEc:dummy"
    res = repec.get_jel_codes(item_id)
    assert isinstance(res, RepecJelResult)
    assert isinstance(res.error, RepecError)
    assert len(res.data) == 0


@patch("requests.Session.get", side_effect=mocked_empty_test)
def test_get_ref_empty(mck) -> None:
    """Testing method for item authors."""
    item_id = "someitemid"
    repec = Repec("somecode")
    res = repec.get_ref(item_id)
    assert isinstance(res, RepecSingleResult)
    assert res.error is not None
    assert res.data == {}


@patch("requests.Session.get", side_effect=mocked_requests)
def test_get_ref(mck) -> None:
    """Testing method for item authors."""
    item_id = "someitemid"
    repec = Repec("somecode")
    res = repec.get_ref(item_id)
    assert isinstance(res, RepecSingleResult)
    assert res.data == {"key": "value"}
    assert res.error is None


@patch("requests.Session.get")
def test_get_error(mock_get) -> None:
    mock_get.return_value = MockResponse(
        ERROR_LOOKUP_URL,
        [],
        text=(
            "<h1>RePEc API Error lookup</h1>"
            "Error 1 applies to function <b>code</b>: User code is missing"
            '<p><a href="https://ideas.repec.org/api.html">Back</a>.'
        ),
    )
    repec = Repec("somecode")

    assert repec.get_error(1) == ("code", "User code is missing")
    mock_get.assert_called_once_with(
        ERROR_LOOKUP_URL, params={"code": "somecode", "number": 1}
    )


@patch("requests.Session.get")
def test_get_error_with_unexpected_response(mock_get) -> None:
    mock_get.return_value = MockResponse(
        ERROR_LOOKUP_URL, [], text="<html>Unexpected response</html>"
    )
    repec = Repec("somecode")

    assert repec.get_error(1) == (
        "N/A",
        "Impossible to get error information from RePEc.",
    )
