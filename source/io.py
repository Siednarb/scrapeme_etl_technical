import os
import csv
import boto3
import datetime
from .config import getConfigField

def saveData(bookDataList,fileNumber):
    '''saves data either locally or to an S3 bucket, depending on config settings'''

    if getConfigField('storage')=="local":
        saveData_local(bookDataList,fileNumber)
    elif getConfigField('storage')=="s3":
        saveData_S3(bookDataList,fileNumber)
    else:
        raise Exception("Invalid config storage parameter (should be 'local' or 'S3')")

def saveData_local(bookDataList,fileNumber):

    filename = getFilenameAndPathFromNumber(fileNumber)
    with open(filename,'w') as f:
        writer = csv.writer(f)

        # table header
        columnNames = list(sorted(bookDataList[0]))
        writer.writerow(columnNames)

        # table body
        for bookData in bookDataList:
            row = [ bookData[key] for key in sorted(bookData) ]
            writer.writerow(row)

def saveData_S3(bookDataList,fileNumber):
    '''saves data to an Amazon S3 bucket, temporarily storing the
    data on the local hard drive until the upload is complete'''

    saveData_local(bookDataList,fileNumber)
    pushData_S3(bookDataList,fileNumber)
    deleteData_local(fileNumber)

def deleteData_local(fileNumber):

    filename = getFilenameAndPathFromNumber(fileNumber)
    if os.path.exists(filename):
        os.remove(filename)

def pushData_S3(bookDataList,fileNumber):
    '''copies a local file up to an S3 bucket defined in the config.json file'''

    filename = getFilenameAndPathFromNumber(fileNumber)
    client = connectToS3()
    if not thisFileAlreadyExistsOnS3(fileNumber,client):
        uploadFileToS3(client,fileNumber)

def connectToS3():
    '''connect to an AWS S3 bucket defined in the config.json file'''

    return boto3.client(
        's3',
        aws_access_key_id=getConfigField('S3 credentials','AWS access key'),
        aws_secret_access_key=getConfigField('S3 credentials','AWS secret')
    )

def thisFileAlreadyExistsOnS3(fileNumber,client):

    aws_objects = client.list_objects_v2(Bucket=getConfigField('S3 credentials','bucket name'))
    if 'Contents' in aws_objects:
        if getFilenameFromNumber(fileNumber) in [ obj['Key'][:24] for obj in aws_objects['Contents'] ]:
            return True
    return False

def uploadFileToS3(client,fileNumber):

    client.upload_file(
        getFilenameAndPathFromNumber(fileNumber),
        getConfigField('S3 credentials','bucket name'),
        getFilenameFromNumber(fileNumber)+getFilenameSuffix(),
        ExtraArgs={'ServerSideEncryption':'AES256','StorageClass':'STANDARD_IA'}
    )

def getFilenameFromNumber(fileNumber):

    return f"Kyle_Horn_books_{str(fileNumber).zfill(2)}_of_{getConfigField('scrape','end page')}"

def getFilenameAndPathFromNumber(fileNumber):

    return f"./data/"+getFilenameFromNumber(fileNumber)

def getFilenameSuffix():

    return '_'+datetime.datetime.now().strftime('%d-%m-%Y-%H-%M')