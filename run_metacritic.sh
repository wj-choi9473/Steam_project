cd metacritic_scraper/metacritic
scrapy crawl metacritic_products -o ../data/crawled_data/metacritic_products.csv
python metaciritic_review_scraper.py
scrapy crawl metacritic_userinfo -o ../data/crawled_data/metacritic_userinfo.csv 