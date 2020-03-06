import csv
from .config import getConfigField

def saveData(bookDataList,fileNumber):
    '''saves data either locally or to an S3 bucket, depending on config settings'''

    if getConfigField('storage')=="local":
        saveData_local(bookDataList,fileNumber)
    elif getConfigField('storage')=="local":
        saveData_S3(bookDataList,fileNumber)
    else:
        raise Exception("Invalid config storage parameter (should be 'local' or 'S3')")

def saveData_local(bookDataList,fileNumber):

    with open(f"./data/Kyle_Horn_books_{str(fileNumber).zfill(2)}_of_{getConfigField('scrape','end page')}.csv",'w') as f:
        writer = csv.writer(f)

        # table header
        columnNames = list(sorted(bookDataList[0]))
        writer.writerow(columnNames)

        # table body
        for bookData in bookDataList:
            row = [ bookData[key] for key in sorted(bookData) ]
            writer.writerow(row)

def saveData_S3(bookDataList,fileNumber):
    raise Exception("Not yet implemented")