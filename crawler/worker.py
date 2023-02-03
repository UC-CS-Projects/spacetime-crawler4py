from threading import Thread
from inspect import getsource
from utils.download import download
from utils import get_logger
from bs4 import BeautifulSoup
import scraper
import time
import nltk, re
from collections import Counter
import PartA, PartB


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)

    def find_intersection(self, list_of_resp, curr_resp):
        if curr_resp.status != 200:
            return False# This webpage's status is not 200 so should not be added.
        for i in list_of_resp:
            tok1 = scraper.cust_tokenize(i)
            tok2 = scraper.cust_tokenize(curr_resp) 
            freq1 = Counter(tok1)
            freq2 = Counter(tok2)
            keys1 = set(freq1) 
            keys2 = set(freq2) 
            inter = keys1.intersection(keys2)
            #Need to check if exact duplicate first
            if len(inter) == len(keys1) or len(inter) == len(keys2):
                return False
            if len(inter) > 1000:
                return False #false means this url is essentially a duplicate webpage
        return True
        
    def run(self):
        #visited_webpages = set()
        list_of_resp = []
        new_visited_links = set()
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            if self.find_intersection(list_of_resp, resp): #call find_intersection to detect duplicate webpages
                list_of_resp.append(resp) #IN THE CASE IT IS NOT A DUPLICATE, APPEND THE NEW UNIQUE WEBPAGE
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                    new_visited_links.add(scraped_url) #should handle infinite traps. does not account for session IDs and URL
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
    
