import os
import re
import bs4
import csv
import requests

def _textIsFloat(text):
    '''helper function to check if a piece of text can be converted to a float'''

    try:
        float(text)
        return True
    except:
        return False

# get the site to scrape book info from
url = "http://books.toscrape.com/catalogue/page-{}.html"
response = requests.get(url.format(1))
assert(response.status_code==200) # ensure the page correctly loaded

# find the HTML containers holding book information
soup = bs4.BeautifulSoup(response.text,features='html.parser')
bookContainers = soup.find_all('article')
assert(len(bookContainers)==20) # enforce the 20 book max rule

# for every book we find on the main page, scrape data
bookDataList = []
for book in bookContainers:
    bookData = {}

    bookData['Main Page Raw HTML'] = soup.text

    # extract book title
    titles = book.find_all('a',title=True) #Note: this is the same call as in the "extract book links" code block below. For a more computationally intensive scrape, I wouldn't do this, but in this case I'd prefer for each piece of data to be isolated to make testing cleaner.
    assert(len(titles)>0) # we must find at least one link per book
    title = titles[0]['title'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
    bookData['Title'] = title

    # extract book links
    links = book.find_all('a',href=True)
    assert(len(links)>0) # we must find at least one link per book
    link = links[0]['href'] #Note: for a more robust scraper, we should check to make sure all of the links match up, instead of simply taking the first
    assert(link.split('.')[-1] in ['html','htm']) # ensure that our scraped link is truly a website
    bookData['Sub-Page Link'] = link

    # extract book ratings
    starRatingScores = {'one':1,'two':2,'three':3,'four':4,'five':5}
    starRatings = book.select('p[class*="star-rating"]')
    assert(len(starRatings)==1) # there should be only one rating per book
    starRating = starRatings[0]['class']
    assert(len(starRating)==2) # this should be a list; the first element is 'star-rating', the second is the rating itself
    starRatingText = starRating[1].lower().strip()
    assert(starRatingText in starRatingScores) # we must recognize the rating, so we can cast it from a string to a number
    bookData['Rating'] = starRatingScores[starRatingText]

    # extract book availability
    availabilities = book.find_all('p',class_="instock availability")
    assert(len(availabilities)==1) # each book should have only one availability
    availabilityText = availabilities[0].text
    bookData['Available'] = availabilityText.strip().lower() == "in stock" # this might be too draconian for a real scrape, and should probably have more sophisticated logic to handle different possible cases

    # extract book thumbnail
    thumbnails = book.find_all('img',class_="thumbnail",src=True)
    assert(len(thumbnails)==1) # each book should only have one thumbnail
    thumbnail = thumbnails[0]['src']
    assert(thumbnail.split('.')[-1] in ['jpg','jpeg','png']) # ensure that the thumbnail is an image file. Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
    bookData['Thumbnail URL'] = thumbnail

    bookDataList.append(bookData)

# for every book we found before, pull its html page
for bookData in bookDataList:

    # pull up the page for each book
    url = "http://books.toscrape.com/catalogue/"+bookData['Sub-Page Link']
    response = requests.get(url)
    assert(response.status_code==200) # ensure the page correctly loaded
    bookData['Sub-Page Raw HTML'] = response.text

# for every book's page, scrape data
for bookData in bookDataList:

    # everything we need is within the article
    soup = bs4.BeautifulSoup(bookData['Sub-Page Raw HTML'],features='html.parser')
    article = soup.find('article')

    # extract book description
    paragraphs = article.findChildren('p',recursive=False) # the only top-level paragraph in the article is our text
    assert(len(paragraphs)==1) # there should be only one paragraph of text
    paragraph = paragraphs[0].text
    bookData['Product Description'] = paragraph

    # extract book photo
    activeItems = soup.find_all('div',class_='item active')
    assert(len(activeItems)==1) # each book should only have one active item
    photos = activeItems[0].find_all('img',src=True)
    assert(len(photos)==1) # each book should only have one photo
    photo = photos[0]['src']
    assert(photo.split('.')[-1] in ['jpg','jpeg','png']) # ensure that the photo is an image file. Note: this list of image file types is just off the top of my head, and by no means a complete list, as this is just a coding test. In a real production setting it should be researched more thoroughly.
    bookData['Full Photo URL'] = photo

    # extract the subcategory from the page breadcrumbs
    categories = [ a.text for a in  soup.find_all('a',href=True) if '../category/books/' in a['href'] ]
    assert(len(categories)==1) # there should only be one sub-category
    bookData['Product Sub-Category'] = categories[0]

    # extract the data table
    tables = article.find_all('table')
    assert(len(tables)==1) # there should only be one table on this page
    table = tables[0]
    tableDict = dict( (row.find('th').text,row.find('td').text) for row in table.find_all('tr') )
    
    # extract simple text fields
    for textField in ['UPC','Product Type']:
        assert(textField in tableDict) # we need the data to exist in the table
        bookData[textField] = tableDict[textField]

    # extract money fields
    for priceField in ['Price (excl. tax)', 'Price (incl. tax)', 'Tax']:
        assert(priceField in tableDict) # we need the data to exist in the table
        priceText = tableDict[priceField]
        assert('£' in priceText) # the price must have a currency symbol. Note: in a production environment we may want to check for other currency symbols, as well.
        price = priceText.split('£')[1]
        assert(_textIsFloat(price))
        bookData[priceField] = float(price)

    # extract availability count
    assert('Availability' in tableDict) # we need the data to exist in the table
    if bookData['Available']:
        inventories = re.findall('\(([0-9]*) available\)',tableDict['Availability'])
        assert(len(inventories)==1)
        bookData['Inventory'] = int(inventories[0])
    else:
        bookData['Inventory'] = 0
    
print(bookData)