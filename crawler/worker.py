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
import urllib.robotparser
from urllib.parse import urlparse




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
        """
        Compares for similarity between the current resp object and all other that have been scraped

        :param list_of_resp: List of all resp object previously added to list container
        :param curr_resp: Current resp object needing to be compared
        :return: False if duplicate, True if not
        """
        # This webpage's status is not 200 so should not be added
        if curr_resp.status != 200:
            return False 
        
        # Goes through all resp objects and compares to find similarities
        for i in list_of_resp:
            # Tokenizes current resp object with iterated object
            tok1, tok2 = scraper.cust_tokenize(i), scraper.cust_tokenize(curr_resp) 

            # Initializes Counter object
            freq1, freq2 = Counter(tok1), Counter(tok2)

            # Creates set of unique Counter values and checks for intersection between keys
            keys1, keys2 = set(freq1), set(freq2) 
            intersect = keys1.intersection(keys2)

            # Checks for exact duplicates first, then if similar
            if len(intersect) == len(keys1) or len(intersect) == len(keys2):
                return False
            if len(intersect) / len(keys1.union(keys2)) > 0.8:
                return False
        return True
        
    def run(self):
        #visited_webpages = set()
        list_of_resp = []
        new_visited_links = set()

        valid_domains = {}# keys will be the unique subdomains. #values would be a tuple. (sitemaps, disallow List, DISALLOWED Entire domain)

        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            #if scraper.robots_text_file(tbd_url, valid_domains, self.config, self.logger):
            scraped_urls = scraper.scraper(tbd_url, resp)
            #if self.find_intersection(list_of_resp, resp): #call find_intersection to detect duplicate webpages
            list_of_resp.append(resp) #IN THE CASE IT IS NOT A DUPLICATE, APPEND THE NEW UNIQUE WEBPAGE
            for scraped_url in scraped_urls:
                if scraped_url not in new_visited_links:
                    self.frontier.add_url(scraped_url)
                    new_visited_links.add(scraped_url) #should handle infinite traps. does not account for session IDs and URL
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
    
    def run(self):
        """
        
        """
        list_of_resp = []
        new_visited_links = set()

        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            resp = download(tbd_url, self.config, self.logger)

            if resp and resp.status == 200 and resp.raw_response:
                for k,v in self.most_common_words:
                    this_resp = scraper.get_top_common_words(resp)
                    if k in this_resp:
                        self.most_common_words[k] = v +this_resp[k]
            url_is_parsed = urlparse(resp.url)
            url_is_parsed = url_is_parsed.hostname
            if url_is_parsed in self.unique_subdomains:
                self.unique_subdomains[url_is_parsed] +=1
            else:
                self.unique_subdomains[url_is_parsed] =1

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            scraped_urls = scraper.scraper(tbd_url, resp)

            if self.find_intersection(list_of_resp, resp): #call find_intersection to detect duplicate webpages
                list_of_resp.append(resp) #IN THE CASE IT IS NOT A DUPLICATE, APPEND THE NEW UNIQUE WEBPAGE
                for scraped_url in scraped_urls:
                    
                    if self.len_curr_longest_webpage < scraper.get_pg_length(scraped_url):
                        self.curr_longest_webpage = scraped_url
                        self.len_curr_longest_webpage = scraper.get_pg_length(scraped_url)
                    if scraped_url not in new_visited_links:
                        self.frontier.add_url(scraped_url)
                        new_visited_links.add(scraped_url) #should handle infinite traps. does not account for session IDs and URL
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        print(scraper.top_fifty_words(self.most_common_words)) #prints the top 50 list of all the words from most frequent to least frequent
        print(self.unique_subdomains)