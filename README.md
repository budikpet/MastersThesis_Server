# Masters thesis server
[![Build Status](https://travis-ci.com/budikpet/MastersThesis_Server.svg?branch=master)](https://travis-ci.com/budikpet/MastersThesis_Server)
  
## Create the server in Heroku
The server uses a [Heroku Scheduler addon](https://devcenter.heroku.com/articles/scheduler) and a [background worker](https://devcenter.heroku.com/articles/python-rq) for scheduling long running tasks. It's used here primarily for automatic web scraping of Zoo Prague lexicon and downloading updated OSM map tiles. 