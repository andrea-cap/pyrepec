# -*- coding: utf-8 -*-
import unittest
from os import environ as os_env

from pyrepec import Repec
from pyrepec.models import (
    RepecError,
    RepecJelResult,
    RepecResultList,
    RepecSingleResult,
)


class TestRepecMethods(unittest.TestCase):
    def setUp(self):

        try:
            token = os_env["REPEC_TOKEN"]
        except KeyError:
            # msg = "Please make sure that 'REPEC_TOKEN' is configured as environment variable."
            # raise KeyError(msg) from err
            raise unittest.SkipTest("No REPEC_TOKEN, skipping integration tests.")

        # Init repec object.
        self.test_repec = Repec(token)

    def test_org_authors(self) -> None:
        """Testing method for authors in organization."""

        org_id = "RePEc:edi:bdigvit"
        res = self.test_repec.get_org_authors(org_id)
        self.assertIsInstance(res, RepecResultList)
        self.assertIsNone(res.error)
        self.assertTrue(len(res.data) > 0)

        # No authors found here so we expect a RepecError.
        item_id = "RePEc:dummy"
        res = self.test_repec.get_org_authors(item_id)
        self.assertIsInstance(res, RepecResultList)
        self.assertIsInstance(res.error, RepecError)
        self.assertTrue(len(res.data) == 0)

    def test_author_data(self) -> None:
        """Testing method for author data."""

        author_id = "pma3331"
        res = self.test_repec.get_author_data(author_id)
        self.assertIsInstance(res, RepecSingleResult)
        self.assertIsNone(res.error)
        self.assertIsNotNone(res.data)

        # No author found here so we expect a RepecError.
        item_id = "RePEc:dummy"
        res = self.test_repec.get_author_data(item_id)
        self.assertIsInstance(res, RepecSingleResult)
        self.assertIsInstance(res.error, RepecError)
        self.assertTrue(len(res.data) == 0)

    def test_authors_for_item(self) -> None:
        """Testing method for item authors."""

        item_id = "RePEc:bis:bisifc:59-21"
        res = self.test_repec.get_authors_for_item(item_id)
        self.assertIsInstance(res, RepecResultList)
        self.assertIsNone(res.error)
        self.assertTrue(len(res.data) > 0)

        # No authors found here so we expect a RepecError.
        item_id = "RePEc:dummy"
        res = self.test_repec.get_authors_for_item(item_id)
        self.assertIsInstance(res, RepecResultList)
        self.assertIsInstance(res.error, RepecError)
        self.assertTrue(len(res.data) == 0)

    def test_jel_codes(self) -> None:
        """Testing method for JEL codes."""

        item_id = "RePEc:eee:labeco:v:83:y:2023:i:c:s0927537123000787"
        res = self.test_repec.get_jel_codes(item_id)
        self.assertIsInstance(res, RepecJelResult)
        self.assertIsNone(res.error)
        self.assertTrue(len(res.data) > 0)

        # No JEL codes found here, we expect a RepecError.
        item_id = "RePEc:dummy"
        res = self.test_repec.get_jel_codes(item_id)
        self.assertIsInstance(res, RepecJelResult)
        self.assertIsInstance(res.error, RepecError)
        self.assertTrue(len(res.data) == 0)

    def test_get_ref(self) -> None:
        item_id = "RePEc:eee:jmacro:v:65:y:2020:i:c:s0164070420301646"
        res = self.test_repec.get_ref(item_id)
        self.assertIsInstance(res, RepecSingleResult)
        self.assertIsNone(res.error)
        self.assertTrue(len(res.data))

    def test_get_ref_empty(self) -> None:
        item_id = "NON_ESISTO"
        res = self.test_repec.get_ref(item_id)
        self.assertIsInstance(res, RepecSingleResult)
        self.assertIsInstance(res.error, RepecError)
        self.assertTrue(len(res.data) == 0)

    def test_errors(self) -> None:
        """Testing method for errors."""

        err_code = 1
        err_func, err_msg = self.test_repec.get_error(err_code)
        self.assertEqual(err_func, "code")
        self.assertEqual(err_msg, "User code is missing")


if __name__ == "__main__":
    unittest.main()
