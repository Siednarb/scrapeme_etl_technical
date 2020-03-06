import os
import re
import bs4
import csv
import requests
from tqdm import tqdm

def _textIsFloat(text):
    '''helper function to check if a piece of text can be converted to a float'''

    try:
        float(text)
        return True
    except:
        return False

def dataValidationAssert(assertBool,errorMessage,scrapeNumber,bookData):
    if not assertBool:
        bookTitle = bookData['Title'] if 'Title' in bookData else ''
        raise Exception(errorMessage + f' [scrapeNumber={scrapeNumber}][bookTitle={bookTitle}]')

for scrapeNumber in range(1,50+1):

    if os.path.exists(f"./data/Kyle_Horn_books_{scrapeNumber}_of_50.csv"):
        continue

    # get the site to scrape book info from
    url = "http://books.toscrape.com/catalogue/page-{}.html"
    response = requests.get(url.format(scrapeNumber))
    dataValidationAssert(response.status_code==200,f"ERROR: Page did not load correctly (status code {response.status_code})",scrapeNumber,{})

    # find the HTML containers holding book information
    soup = bs4.BeautifulSoup(response.text,features='html.parser')
    bookContainers = soup.find_all('article')
    dataValidationAssert(len(bookContainers)<=20,f"ERROR: Too many books scraped (scraped {len(bookContainers)})",scrapeNumber,{})
    dataValidationAssert(len(bookContainers)>=20,f"ERROR: Too few books scraped (scraped {len(bookContainers)})",scrapeNumber,{})

    # for every book we find on the main page, scrape data
    bookDataList = []
    for book in tqdm(bookContainers):
        bookData = {}

        bookData['Main Page Raw HTML'] = soup.text

        # extract book title
        titles = book.find_all('a',title=True) #Note: this is the same call as in the "extract book links" code block below. For a more computationally intensive scrape, I wouldn't do this, but in this case I'd prefer for each piece of data to be isolated to make testing cleaner.
        dataValidationAssert(len(titles)>0, "ERROR: No title found",scrapeNumber,bookData)
        title = titles[0]['title'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
        bookData['Title'] = title

        # extract book links
        links = book.find_all('a',href=True)
        dataValidationAssert(len(links)>0,"ERROR: No book sub-link found",scrapeNumber,bookData)
        link = links[0]['href'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
        dataValidationAssert(link.split('.')[-1] in ['html','htm'],"ERROR: Book sub-page link lacks an HTML extension",scrapeNumber,bookData)
        bookData['Sub-Page Link'] = link

        # extract book ratings
        starRatingScores = {'one':1,'two':2,'three':3,'four':4,'five':5}
        starRatings = book.select('p[class*="star-rating"]')
        dataValidationAssert(len(starRatings)==1, "ERROR: Star rating missing or duplicated",scrapeNumber,bookData)
        starRating = starRatings[0]['class']
        dataValidationAssert(len(starRating)==2,"ERROR: Malformed star rating",scrapeNumber,bookData) # this should be a list; the first element is 'star-rating', the second is the rating itself
        starRatingText = starRating[1].lower().strip()
        dataValidationAssert(starRatingText in starRatingScores, "ERROR: Star rating value not readable",scrapeNumber,bookData) # we must recognize the rating, so we can cast it from a string to a number
        bookData['Rating'] = starRatingScores[starRatingText]

        # extract book availability
        availabilities = book.find_all('p',class_="instock availability")
        dataValidationAssert(len(availabilities)==1,"ERROR: Book availability missing or duplicated",scrapeNumber,bookData)
        availabilityText = availabilities[0].text
        bookData['Available'] = availabilityText.strip().lower() == "in stock" # this might be too draconian for a real scrape, and should probably have more sophisticated logic to handle different possible cases

        # extract book thumbnail
        thumbnails = book.find_all('img',class_="thumbnail",src=True)
        dataValidationAssert(len(thumbnails)==1,"ERROR: Book thumbnail missing or duplicated",scrapeNumber,bookData)
        thumbnail = thumbnails[0]['src']
        dataValidationAssert(thumbnail.split('.')[-1] in ['jpg','jpeg','png'],"ERROR: Book thumbnail filename is not a known image format",scrapeNumber,bookData) # ensure that the thumbnail is an image file. Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
        bookData['Thumbnail URL'] = thumbnail

        bookDataList.append(bookData)

    ## for every book we found before, pull its html page
    #for bookData in bookDataList:

        # pull up the page for each book
        url = "http://books.toscrape.com/catalogue/"+bookData['Sub-Page Link']
        response = requests.get(url)
        dataValidationAssert(response.status_code==200,f"ERROR: Book sub-page did not load correctly (status code {response.status_code})",scrapeNumber,bookData)
        bookData['Sub-Page Raw HTML'] = response.text

    ## for every book's page, scrape data
    #for bookData in bookDataList:

        # everything we need is within the article
        soup = bs4.BeautifulSoup(bookData['Sub-Page Raw HTML'],features='html.parser')
        article = soup.find('article')

        # extract book description
        if 'Product Description' in [ h2.text for h2 in soup.find_all('h2') ]:
            paragraphs = article.findChildren('p',recursive=False) # the only top-level paragraph in the article is our text
            dataValidationAssert(len(paragraphs)==1,"ERROR: Product description missing or duplicated",scrapeNumber,bookData)
            paragraph = paragraphs[0].text
            bookData['Product Description'] = paragraph
        else:
            bookData['Product Descrption'] = None

        # extract book photo
        activeItems = soup.find_all('div',class_='item active')
        dataValidationAssert(len(activeItems)==1,"ERROR: Book activte item missing or duplicated",scrapeNumber,bookData)
        photos = activeItems[0].find_all('img',src=True)
        dataValidationAssert(len(photos)==1,"ERROR: Book photo missing or duplicated",scrapeNumber,bookData)
        photo = photos[0]['src']
        dataValidationAssert(photo.split('.')[-1] in ['jpg','jpeg','png'],"ERROR: Book full image filename is not a known image format",scrapeNumber,bookData) #Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
        bookData['Full Photo URL'] = photo

        # extract the subcategory from the page breadcrumbs
        categories = [ a.text for a in  soup.find_all('a',href=True) if '../category/books/' in a['href'] ]
        dataValidationAssert(len(categories)==1,"ERROR: Breadcrumbs sub-category missing or duplicated",scrapeNumber,bookData)
        bookData['Product Sub-Category'] = categories[0]

        # extract the data table
        tables = article.find_all('table')
        dataValidationAssert(len(tables)==1,"ERROR: Sub-page data table missing or duplicated",scrapeNumber,bookData)
        table = tables[0]
        tableDict = dict( (row.find('th').text,row.find('td').text) for row in table.find_all('tr') )
        
        # extract simple text fields
        for textField in ['UPC','Product Type']:
            dataValidationAssert(textField in tableDict,f"ERROR: text field '{textField}' missing from table",scrapeNumber,bookData)
            bookData[textField] = tableDict[textField]

        # extract money fields
        for priceField in ['Price (excl. tax)', 'Price (incl. tax)', 'Tax']:
            dataValidationAssert(priceField in tableDict,f"ERROR: price field '{priceField}' missing from table",scrapeNumber,bookData)
            priceText = tableDict[priceField]
            dataValidationAssert('£' in priceText,f"ERROR: price field '{priceField}' missing GBP symbol",scrapeNumber,bookData) #Note: in a production environment we may want to check for other currency symbols, as well.
            price = priceText.split('£')[1]
            dataValidationAssert(_textIsFloat(price),f"ERROR: price field '{priceField}' cannot be cast to a float",scrapeNumber,bookData)
            bookData[priceField] = float(price)

        # extract availability count
        dataValidationAssert('Availability' in tableDict,"ERROR: Book availability missing from table",scrapeNumber,bookData)
        if bookData['Available']:
            inventories = re.findall('\(([0-9]*) available\)',tableDict['Availability'])
            dataValidationAssert(len(inventories)==1,"ERROR: Book inventory quantity (inside availability string) is missing or duplicated",scrapeNumber,bookData)
            bookData['Inventory'] = int(inventories[0])
        else:
            bookData['Inventory'] = 0
    
    # save book data
    if not os.path.exists("./data/"):
        os.mkdir("./data/")
    with open(f"./data/Kyle_Horn_books_{scrapeNumber}_of_50.csv",'w') as f:
        writer = csv.writer(f)

        # table header
        columnNames = list(sorted(bookData))
        writer.writerow(columnNames)

        # table body
        for bookData in bookDataList:
            row = [ bookData[key] for key in sorted(bookData) ]
            writer.writerow(row)