import os
from .config import getConfigField

def initializeProjectFoldersIfNotInitialized():
    '''initializes folders necessary for the project, if they aren't
    already initialized'''

    for folder in ['data','error']:
        if not os.path.exists(f"./{folder}/"):
            os.mkdir(f"./{folder}/")

def getNextFileNumberToScrape():
    '''returns the next file number to generate a CSV file for. If all files are generated,
    then simply return None'''

    init,final = getConfigField('scrape','start page'),getConfigField('scrape','end page')
    fileTemplate = "./data/Kyle_Horn_books_{init}_of_{final}.csv".format(init='{}',final=final)
    allFileNumbers = [ fileTemplate for fileNumber in range(init,final+1) ]
    targetFileNumbers = [ fileNumber
                          for fileNumber in range(init,final+1) 
                          if not os.path.exists(fileTemplate.format(str(fileNumber).zfill(2))) ]
    if len(targetFileNumbers)>0:
        return targetFileNumbers[0]
    else:
        return None