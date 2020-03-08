import pickle
import unittest
from source.scrape import scrapeDataMainPage,scrapeDataSubPages
from source.initialization import initializeProjectFoldersIfNotInitialized,getNextFileNumberToScrape

#bookDataList = (fileNumber,bookDataList)

class Test(unittest.TestCase):
    
    def test_scrapeDataMainPage_via_data_validation_asserts(self):
        bookDataList = scrapeDataMainPage(fileNumber=1,isTest=True)

        with open("./test/scrapeDataMainPage_test.pickle",'wb') as f:
            pickle.dump(bookDataList,f)
        self.assertTrue(True)

    def test_scrapeDataSubPages(self):

        with open("./test/scrapeDataMainPage_test.pickle",'rb') as f:
            bookDataList = pickle.load(f)
        scrapeDataSubPages(fileNumber=1,bookDataList=bookDataList)
        self.assertTrue(True)

if __name__=="__main__":
    unittest.main()