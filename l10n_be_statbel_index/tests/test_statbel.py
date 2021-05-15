# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os

import requests_mock

from odoo.tests import SavepointCase

directory = os.path.dirname(__file__)


class TestStatBel(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard = cls.env["l10n_be.statbel.retrieval"].create({})
        cls.index = cls.env["l10n_be.statbel.index"]

    def test_statbel(self):
        indexes_before = self.index.search_count([])
        self.wizard.retrieve_statbel()
        with requests_mock.mock() as r_mock:
            path = os.path.join(directory, "CPI All base years.xlsx")
            with open(path, "rb") as the_file:
                r_mock.get(self.wizard.url, body=the_file)
                self.wizard.retrieve_statbel()
        indexes_after = self.index.search_count([])
        self.assertTrue(indexes_before < indexes_after)
