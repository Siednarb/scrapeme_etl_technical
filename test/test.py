import pickle
import unittest
from source.scrape import scrapeDataMainPage,scrapeDataSubPages
from source.initialization import initializeProjectFoldersIfNotInitialized,getNextFileNumberToScrape

class Test(unittest.TestCase):
    
    def test_scrapeDataMainPage_via_data_validation_asserts(self):
        scrapeDataMainPage(fileNumber=1,isTest=True)
        self.assertTrue(True) # if we make it here, we've survived 16 dataValidationAssert() calls

    def test_scrapeDataSubPages(self):

        with open("./test/scrapeDataMainPage_test.pickle",'rb') as f:
            bookDataList_verify = pickle.load(f)
        scrapeDataSubPages(fileNumber=1,bookDataList=bookDataList)
        self.assertTrue(True) # if we make it here, we've survived 10 dataValidationAssert() calls

if __name__=="__main__":
    unittest.main()