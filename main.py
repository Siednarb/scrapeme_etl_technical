from source.initialization import initializeProjectFoldersIfNotInitialized,getNextFileNumberToScrape
from source.scrape import scrapeDataMainPage,scrapeDataSubPages
from source.io import saveData

if __name__=="__main__":

    initializeProjectFoldersIfNotInitialized()
    fileNumber = getNextFileNumberToScrape()
    if fileNumber is not None:
        bookDataList = scrapeDataMainPage(fileNumber)
        bookDataList = scrapeDataSubPages(fileNumber,bookDataList)
        saveData(bookDataList,fileNumber)