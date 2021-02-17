# Masters thesis server

  
## Create the server in Heroku
The server uses a [custom scheduler process](https://devcenter.heroku.com/articles/scheduled-jobs-custom-scheduler-processes) and a [background worker](https://devcenter.heroku.com/articles/python-rq) which enable scheduling of long running tasks. It's used here primarily for automatic web scraping of Zoo Prague lexicon and downloading updated OSM map tiles. 