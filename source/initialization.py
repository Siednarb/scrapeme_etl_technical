import os
from .config import getConfigField
from .io import connectToS3,thisFileAlreadyExistsOnS3

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
    fileTemplate = "./data/Kyle_Horn_books_{init}_of_{final}".format(init='{}',final=final)
    allFileNumbers = [ fileTemplate for fileNumber in range(init,final+1) ]
    if getConfigField('storage') == 'local':
        targetFileNumbers = [ fileNumber
                              for fileNumber in range(init,final+1) 
                              if not os.path.exists(fileTemplate.format(str(fileNumber).zfill(2))) ]
    elif getConfigField('storage') == 's3':
        client = connectToS3()
        targetFileNumbers = [ fileNumber
                              for fileNumber in range(init,final+1) 
                              if not thisFileAlreadyExistsOnS3(fileNumber,client) ]
    else:
        raise Exception("Invalid form of storage")

    if len(targetFileNumbers)>0:
        return targetFileNumbers[0]
    else:
        return None