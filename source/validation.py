import json
import datetime

def textIsFloat(text):
    '''helper function to check if a piece of text can be converted to a float'''

    try:
        float(text)
        return True
    except:
        return False

def dataValidationAssert(assertBool,errorMessage,fileNumber,bookData):
    '''gives a descriptive output of encountered errors and save them to an error log'''
    
    if not assertBool:
        bookTitle = bookData['Title'] if 'Title' in bookData else ''
        generateErrorLog(errorMessage,fileNumber,bookTitle)
        raise Exception(errorMessage + f' [fileNumber={fileNumber}][bookTitle={bookTitle}]')

def generateErrorLog(errorMessage,fileNumber,bookTitle):

    errorJson = {
        "message"    : errorMessage,
        "fileNumber" : fileNumber,
        "bookTitle"  : bookTitle
    }

    with open(f"./error/{datetime.datetime.now()}",'w') as f:
        json.dump(errorJson,f,indent=4)