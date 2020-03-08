# Book Site Web Scrape Project

## 1. Project Description

This project is a basic ETL data scraper targeting data from `books.toscrape.com`. The code itself is dockerized, with non-monolithic code partitioned into several files, has error logging for data schema & type changes, some test cases, and can save data either locally or to a specified AWS S3 bucket (where its credentials are set in a config file, and S3 saves include the date and time in their filename). Dependencies are kept to a bare minimum to ease building and deployment.

## 2. Requirements

Here are the following rules for this project:
1. The service is not permitted to scrape more than 20 books at a time.
2. The service can only be run once per 5-minute interval.
3. All 1000 books available on the site must be scraped.
4. The use of `time_out`, `sleep`, `wait`, and similar functions for scheduling is strictly forbidden.
5. All files deposited on AWS S3 should have the following format: `<candidate_name>_books_<fileNumber>_of_50_<timestamp-to-minute-resolution>`
4. Once configured, the service should scrape, mung, and store data on all 1000 books without intervention.

## 3. Dependencies

The project has minimal dependencies, but still relies on the following:
1. A Unix-based system (only tested on Ubuntu 18.04.2 LTS).
2. Docker set up on the system.

## 4. Building

To build the project, simply run `sh build.sh` at the root folder of the project in the terminal. This will get docker to build the project's container.

## 5. Testing

To run the project test cases, use `sh test.sh` after building the docker container. This will perform testing inside the same container used for deployment.

## 6. Deployment

Deploying the project requires the following steps:
1. Copy the `./config/sample config.json` file to `./config/config.json`. The default settings will save data locally without timestamps. To set saving to an S3 bucket, fill out the following fields:
 * "storage" should be set from 'local' to 's3'.
 * All three "S3 credentials" fields should be filled out as per the target S3 bucket.
2. Build the project using docker by running `sh build.sh` in the root folder of the project, and make sure the docker image `book_etl` has been creatd by running `docker images`.
3. Test the project by running `sh test.sh` at the root folder of the project in the terminal.
3. Set cron to run the project regularly at 5 minute intervals:
 * The exact cron string will vary from computer to computer. Run `sh make_cron.sh` and copy the text string it echos to the terminal.
 * Paste the text string in your crontab file. One can access the crontab file by running `crontab -e` at the terminal.

 This should be sufficient to begin the service at the next time divisible by 5 (eg: 9:35, 10:40, 1:15). To stop the service, comment out the cron string inside the crontab file using a `#` at the start of the string.

If the goal is not to deploy the project to download data on all 1000 books, but to run it once to harvest a single file, you can also call `sh run_once.sh` in the root folder of the project at the terminal, and this will download one file containing 20 books.

NOTE: If you need sudo permissions to run docker, then you'll need to run `sudo` for all `sh` commands except `make_cron.sh`.

## 7. Config and Data File Documentation

### 7.a Descriptions for config.json fields

{
    "storage" : The storage location for the data. This can be set either to "local" or "s3". It is case-sensitive.
    "scrape" : {
        "url template" : The url template for where to download book data. The file number (which ranges by default from 1-50) will be injected in place of `{}` in this string,
        "start page" : The first page of the website to begin scraping from (defaults to 1),
        "end page" : The last page of the website to scrape from (defaults to 50).
    },
    "S3 credentials" : {
        "bucket name" : The name of the S3 bucket to deposit data to (eg: "bucket-name"),
        "AWS access key" : A 20 character alphanumeric access key for the S3 bucket,
        "AWS secret" : A 40 digit secret key (that should not normally be shared!) to access the S3 bucket.
    }
}

### 7.b Descriptions for saved data fields

Saved files are in standard comma-separated CSV format. The columns are as follows, with data type in parentheses:

"Available"            : Whether or not the book is available for purchase (bool)
"Inventory"            : The number of available books for purchase (int)
"Full Photo URL"       : The url for the enlarged image of the book (string)
"Thumbnail URL"        : The url for the smaller image of the book (string)
"Price (excl.tax)"     : The price in Pounds (GBP), without tax (float)
"Price (incl.tax)"     : The price in Pounds (GBP), with tax (float)
"Tax"                  : The cost in Pounds (GBP) of the tax (float)
"Product Description"  : A paragraph of descriptive text for the book (string)
"Product Sub-Category" : The type of book, as scraped from the website breadcrumbs (string)
"Product Type"         : The type of product. For all rows this will be "Books" (string)
"Rating"               : A 1-5 rating presumably based on user input (int)
"Sub-Page Link"        : The link to navigate to the book's individual page (string)
"Sub-Page Raw HTML"    : A raw text dump of the HTML for the book's individual page (string)
"UPC"                  : The Universal Product Code for the given book (string)

## 8. Miscellaneous Design Decisions

As with any project, one must decide how much or how little effort constitutes "done". Since this is just a coding test, I've cut a few corners to expidite the production of the product, and have given explanations for my rationale on each cut. In a true production environment, corners wouldn't, shouldn't, and couldn't be cut.

1. There appear to be 20 books per page on the website. One of the requirements is to only scrape 20 books per run of the ETL. For simplicity, I'll take this to mean that I should only scrape one page at a time. However, to keep in the spirit of the assignment, I'll post an error log if the ETL scrapes more than 20 books in a single run.
2. I did not include any code to update saved HTML pages used for tests (located in ./test/). However, in cases where the target page to scrape changes their schema, the test HTML page would need to be updated, and having an automated mechanism to refresh html used for testing is generally preferred.
3. Python's Fabric has far more options than a simple Makefile, but for simplicity's sake (and to reduce compilation dependencies), I've opted for just a simple Makefile.
4. Even though the output is CSV, I still try to cast data to appropriate types wherever possible, to help with data validation.
5. To reduce the complexity of the project, if an error is encountered, the scraper will stop, post an error log, and try again later, discarding any data scraped. In a real production environment, it's worth discussing if partially scraped data should still be pushed to the data lake and filled in on subsequent scrapes, or if that scrape should simply halt and throw an error message (discarding parts of the data scraped successfully until another retry).
6. There are some instances where a piece of data is repeated (eg: the price). In these cases, it would be better to scrape them all and compare them to ensure data consistency. However, this seems a bit excessive for code not actually intended for production, so here I only scrape one version of the data.
7. Since I'm only taking data from one source (see the previous point), When data is available on the main page, I opt to take it rather than data on individual book pages. The logic behind this is as follows: even though I'm stopping when data is missing or unexpectedly formatted, if I weren't, this would ensure I gather as much data as possible if the dedicated page for each book isn't reachable.
8. To avoid spending all night writing unit tests (since my impression was that the assignment was focusing on the ability to set the timing of the scraper job, rather than crafting the perfect scraper code), I've opted for just a few simple test cases. For real production code, I would naturally have full code coverage on unit tests.
9. As part of data validation, I frequently use soup.find_all() instead of soup.find(), even when I plan to take only the first encountered instance of the find. This is to help catch situations where the scraper isn't pulling correctly, rather than letting them flow through undetected.