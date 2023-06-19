import unittest
from pd_lookup import search as pdsearch


class TestgetSearch(unittest.TestCase):
    def test_search_init(self):
        pdlookup = pdsearch.PersonalDevice()

if __name__ == '__main__':
    unittest.main()
