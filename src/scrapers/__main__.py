from sys import argv
import scrapers.zoo_scraper as zoo_scraper
import scrapers.map_downloader as map_downloader
import scrapers.rss_parser as rss_parser

# This code is run when "python -m scrapers" is invoked. Not run when "scrapers" entry_point is used
usage_msg = "Usage: python -m scrapers [zoo_scraper|map_downloader]"
if len(argv) == 2:
    command: str = argv[1]

    if command == 'zoo_scraper':
        zoo_scraper.main()
    elif command == 'map_downloader':
        map_downloader.main()
    elif command == 'rss_parser':
        rss_parser.main()
    else:
        print(usage_msg)
else:
    print(usage_msg)
