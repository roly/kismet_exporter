import unittest
import search


class TestgetSearch(unittest.TestCase):
    def test_search_init(self):
        pdsearch = search.PersonalDevice()
    def test_get_map(self): 
        pdsearch = search.PersonalDevice()
        map = pdsearch.getPDMap()

    def test_search(self):
        pdsearch=search.PersonalDevice()
        result=pdsearch.search('android')
        self.assertEqual(result[0],"hotspot")
        result=pdsearch.search('Uno-bus')
        self.assertEqual(result[0],"other")
        result=pdsearch.search('Uno bus')
        self.assertEqual(result[0],"other")
        self.assertEqual(result[1],"uno.bus")
        result=pdsearch.search("I dont exist")
        self.assertEqual(result[0],"")
        self.assertEqual(result[1],"")
        result=pdsearch.search("something","tesla")
        self.assertEqual(result[0],"car")
        self.assertEqual(result[1],"tesla")

        #first string wins 
        result=pdsearch.search("Uno bus","tesla")
        self.assertEqual(result[0],"other")
        self.assertEqual(result[1],"uno.bus")

        pd,pdm=result=pdsearch.search('android')
        self.assertEqual(pd,'hotspot')
        self.assertEqual(pdm,'android')

        result=pdsearch.search("Rolys iPhone","Apple")
        self.assertEqual(result[0],"hotspot")
        self.assertEqual(result[1],"iphone")





if __name__ == '__main__':
    unittest.main()
