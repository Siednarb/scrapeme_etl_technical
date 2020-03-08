import os
import re
import bs4
import csv
import requests
from tqdm import tqdm

from .config import getConfigField
from .validation import textIsFloat,dataValidationAssert

def scrapeDataMainPage(fileNumber,isTest=False):
    '''this is one of the two main scraping functions. It pulls data from the main books.toscrape.com page'''

    html = getMainPageHTML(isTest,fileNumber)
    bookContainers = partitionMainPageHTMLByBook(html,fileNumber)

    bookDataList = []
    for book in tqdm(bookContainers,desc=f"Main Page [File {fileNumber}]"):
        bookData = {}
        bookData['Title']              = extractBookTitle(book,bookData,fileNumber)
        bookData['Sub-Page Link']      = extractBookLinks(book,bookData,fileNumber)
        bookData['Rating']             = extractBookRating(book,bookData,fileNumber)
        bookData['Available']          = extractBookAvailability(book,bookData,fileNumber)
        bookData['Thumbnail URL']      = extractBookThumbnailURL(book,bookData,fileNumber)
        bookData['Sub-Page Raw HTML']  = getBookSubPage(bookData,fileNumber,isTest)
        bookDataList.append(bookData)
    return bookDataList

def scrapeDataSubPages(fileNumber,bookDataList):
    '''this is one of the two main scraping functions. It pulls data from the individual pages for each book'''

    for bookData in tqdm(bookDataList,desc=f"Sub Page [File {fileNumber}]"):
        soup = getBookSubPageSoup(bookData)
        bookData['Product Description']  = extractBookDescription(soup,bookData,fileNumber)
        bookData['Full Photo URL']       = extractBookPhotoURL(soup,bookData,fileNumber)
        bookData['Product Sub-Category'] = extractBreadcrumbsSubcategory(soup,bookData,fileNumber)
        tableDict = extractDataTable(soup,bookData,fileNumber)
        extractDataTableTextFields(tableDict,bookData,fileNumber)   
        extractDataTablePriceFields(tableDict,bookData,fileNumber)
        extractAvailabilityQtyAkaInventoryCount(tableDict,bookData,fileNumber)
    return bookDataList

def getMainPageHTML(isTest,fileNumber):
    if isTest:    
        with open("./test/test_page.html",'r') as f:
            text = f.read()
        return text
    else:
        response = requests.get(getConfigField('scrape','url template').format(fileNumber))
        dataValidationAssert(response.status_code==200,f"ERROR: Page did not load correctly (status code {response.status_code})",fileNumber,{})
        return response.text

def partitionMainPageHTMLByBook(html,fileNumber):
    soup = bs4.BeautifulSoup(html,features='html.parser')
    bookContainers = soup.find_all('article')
    dataValidationAssert(len(bookContainers)<=20,f"ERROR: Too many books scraped (scraped {len(bookContainers)})",fileNumber,{})
    dataValidationAssert(len(bookContainers)>=20,f"ERROR: Too few books scraped (scraped {len(bookContainers)})",fileNumber,{})
    return bookContainers

def extractBookTitle(book,bookData,fileNumber):
    titles = book.find_all('a',title=True) #Note: this is the same call as in the "extract book links" code block below. For a more computationally intensive scrape, I wouldn't do this, but in this case I'd prefer for each piece of data to be isolated to make testing cleaner.
    dataValidationAssert(len(titles)>0, "ERROR: No title found",fileNumber,bookData)
    title = titles[0]['title'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
    return title

def extractBookLinks(book,bookData,fileNumber):
    links = book.find_all('a',href=True)
    dataValidationAssert(len(links)>0,"ERROR: No book sub-link found",fileNumber,bookData)
    link = links[0]['href'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
    dataValidationAssert(link.split('.')[-1] in ['html','htm'],"ERROR: Book sub-page link lacks an HTML extension",fileNumber,bookData)
    return link

def extractBookRating(book,bookData,fileNumber):
    starRatingScores = {'one':1,'two':2,'three':3,'four':4,'five':5}
    starRatings = book.select('p[class*="star-rating"]')
    dataValidationAssert(len(starRatings)==1, "ERROR: Star rating missing or duplicated",fileNumber,bookData)
    starRating = starRatings[0]['class']
    dataValidationAssert(len(starRating)==2,"ERROR: Malformed star rating",fileNumber,bookData) # this should be a list; the first element is 'star-rating', the second is the rating itself
    starRatingText = starRating[1].lower().strip()
    dataValidationAssert(starRatingText in starRatingScores, "ERROR: Star rating value not readable",fileNumber,bookData) # we must recognize the rating, so we can cast it from a string to a number
    return starRatingScores[starRatingText]

def extractBookAvailability(book,bookData,fileNumber):
    availabilities = book.find_all('p',class_="instock availability")
    dataValidationAssert(len(availabilities)==1,"ERROR: Book availability missing or duplicated",fileNumber,bookData)
    availabilityText = availabilities[0].text
    return availabilityText.strip().lower() == "in stock" # this might be too draconian for a real scrape, and should probably have more sophisticated logic to handle different possible cases

def extractBookThumbnailURL(book,bookData,fileNumber):
    thumbnails = book.find_all('img',class_="thumbnail",src=True)
    dataValidationAssert(len(thumbnails)==1,"ERROR: Book thumbnail missing or duplicated",fileNumber,bookData)
    thumbnail = thumbnails[0]['src']
    dataValidationAssert(thumbnail.split('.')[-1] in ['jpg','jpeg','png'],"ERROR: Book thumbnail filename is not a known image format",fileNumber,bookData) # ensure that the thumbnail is an image file. Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
    return thumbnail

    bookDataList.append(bookData)

def getBookSubPage(bookData,fileNumber,isTest):
    if isTest:
        with open("./test/sub_test_page.html",'r') as f:
            text = f.read()
        return text
    else:
        url = "http://books.toscrape.com/catalogue/"+bookData['Sub-Page Link']
        response = requests.get(url)
        dataValidationAssert(response.status_code==200,f"ERROR: Book sub-page did not load correctly (status code {response.status_code})",fileNumber,bookData)
        return response.text

def getBookSubPageSoup(bookData):
    return bs4.BeautifulSoup(bookData['Sub-Page Raw HTML'],features='html.parser')

def extractBookDescription(soup,bookData,fileNumber):
    if 'Product Description' in [ h2.text for h2 in soup.find_all('h2') ]:
        paragraphs = soup.find('article').findChildren('p',recursive=False) # the only top-level paragraph in the article is our text
        dataValidationAssert(len(paragraphs)==1,"ERROR: Product description missing or duplicated",fileNumber,bookData)
        paragraph = paragraphs[0].text
        return paragraph
    else:
        return None

def extractBookPhotoURL(soup,bookData,fileNumber):
    activeItems = soup.find_all('div',class_='item active')
    dataValidationAssert(len(activeItems)==1,"ERROR: Book activte item missing or duplicated",fileNumber,bookData)
    photos = activeItems[0].find_all('img',src=True)
    dataValidationAssert(len(photos)==1,"ERROR: Book photo missing or duplicated",fileNumber,bookData)
    photo = photos[0]['src']
    dataValidationAssert(photo.split('.')[-1] in ['jpg','jpeg','png'],"ERROR: Book full image filename is not a known image format",fileNumber,bookData) #Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
    return photo

def extractBreadcrumbsSubcategory(soup,bookData,fileNumber):
    categories = [ a.text for a in  soup.find_all('a',href=True) if '../category/books/' in a['href'] ]
    dataValidationAssert(len(categories)==1,"ERROR: Breadcrumbs sub-category missing or duplicated",fileNumber,bookData)
    return categories[0]

def extractDataTable(soup,bookData,fileNumber):
    tables = soup.find('article').find_all('table')
    dataValidationAssert(len(tables)==1,"ERROR: Sub-page data table missing or duplicated",fileNumber,bookData)
    table = tables[0]
    tableDict = dict( (row.find('th').text,row.find('td').text) for row in table.find_all('tr') )
    return tableDict
    
def extractDataTableTextFields(tableDict,bookData,fileNumber):
    for textField in ['UPC','Product Type']:
        dataValidationAssert(textField in tableDict,f"ERROR: text field '{textField}' missing from table",fileNumber,bookData)
        bookData[textField] = tableDict[textField]

def extractDataTablePriceFields(tableDict,bookData,fileNumber):
    for priceField in ['Price (excl. tax)', 'Price (incl. tax)', 'Tax']:
        dataValidationAssert(priceField in tableDict,f"ERROR: price field '{priceField}' missing from table",fileNumber,bookData)
        priceText = tableDict[priceField]
        dataValidationAssert('£' in priceText,f"ERROR: price field '{priceField}' missing GBP symbol",fileNumber,bookData) #Note: in a production environment we may want to check for other currency symbols, as well.
        price = priceText.split('£')[1]
        dataValidationAssert(textIsFloat(price),f"ERROR: price field '{priceField}' cannot be cast to a float",fileNumber,bookData)
        bookData[priceField] = float(price)

def extractAvailabilityQtyAkaInventoryCount(tableDict,bookData,fileNumber):
    dataValidationAssert('Availability' in tableDict,"ERROR: Book availability missing from table",fileNumber,bookData)
    if bookData['Available']:
        inventories = re.findall('\(([0-9]*) available\)',tableDict['Availability'])
        dataValidationAssert(len(inventories)==1,"ERROR: Book inventory quantity (inside availability string) is missing or duplicated",fileNumber,bookData)
        bookData['Inventory'] = int(inventories[0])
    else:
        bookData['Inventory'] = 0