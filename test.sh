docker run -it -v $PWD/config:/app/config -v $PWD/data/:/app/data/ -v $PWD/error/:/app/error/ --entrypoint python book_etl -m unittest