import unittest
from unittest.mock import mock_open, patch
from src.database import Database
from src import tables

class TestDB(unittest.TestCase):
    def setup(self):
        pass
    def teardown(self):
        pass

    def test_database_string(self):
        config = {'database': 'test', 'database_name': 'test.db', 'database_user': '', 'database_password': '', 'database_host': '', 'database_port': ''}
        db = Database(config)
        self.assertEqual('test://@/test.db', db._get_database_string())