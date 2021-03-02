# Zoo Prague server
[![Build Status](https://travis-ci.com/budikpet/MastersThesis_Server.svg?branch=master)](https://travis-ci.com/budikpet/MastersThesis_Server)

The server is used primarily as a data collector & provider for Zoo Prague iOS application and is part of my Master's thesis. It is hosted on [Heroku](https://budikpet-zoo-prague.herokuapp.com/docs) cloud.

## Features
- Has a webscraping script which uses [Beautifulsoup4](https://pypi.org/project/beautifulsoup4/) library to get data from [Zoo Prague Lexicon](https://www.zoopraha.cz/zvirata-a-expozice/lexikon-zvirat)
- Uses an official script library [tilepacks](https://github.com/tilezen/tilepacks) for downloading map data of Zoo Prague
- Uses MongoDB Atlas cloud using [pymongo](https://github.com/mongodb/mongo-python-driver) library
    - It is possible to easily use any other DB to store main data
- Uses AWS S3 service to store downloaded map data
- Contains a scheduling logic for automating data updates
- Provides a REST API for downloaded data using [FastAPI](https://github.com/tiangolo/fastapi) library

## Local usage
Firstly download the server from GitHub and create a virtual environment. Then install all needed dependencies and server modules using:
```sh
$ pip install -e .
```

To run server locally use:
```sh
$ uvicorn src.rest.main:app
```

### Used environmental variables
| Plugin | README |
| ------ | ------ |
| AWS_ACCESS_KEY_ID | Access key for AWS S3 service. |
| AWS_DEFAULT_REGION | Default region of AWS S3 service. |
| AWS_SECRET_ACCESS_KEY | Secret key for AWS S3 service. |
| AWS_STORAGE_BUCKET_NAME | Name of the AWS S3 bucket where some data is stored. |
| HEROKU_API_KEY | A Heroku Platform API key. |
| MAPZEN_API_KEY | An API key for vector map tiles provider. |
| MAPZEN_URL_PREFIX | An URL prefix for a vector map tiles provider. |
| MIN_SCRAPING_DELAY | Minimum time to wait between two HTTP requests during web scraping. |
| MONGODB_URI | URI of MongoDB database which is used to hold main data. |
| REDISTOGO_URL | A URL for a RedisToGo Heroku plugin which is used by a scheduler to store scheduled work. |

## Automated data updates
The server uses a [Heroku Scheduler addon](https://devcenter.heroku.com/articles/scheduler) and a [background worker](https://devcenter.heroku.com/articles/python-rq) for scheduling long running tasks. It's used here primarily for automatic web scraping of Zoo Prague lexicon and downloading updated OSM map tiles. 