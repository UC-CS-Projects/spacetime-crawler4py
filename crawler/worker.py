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
from bs4 import SoupStrainer
import chardet, lxml


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier

        # Instantiate code to determine longest webpage 
        self.curr_longest_webpage = ''
        self.len_curr_longest_webpage = 0

        # Instantiate code to determine most common words
        self.most_common_words = {}

        # Instantiate code to determine unique subdomains
        self.unique_subdomains = {}
        # Basic check for requests in scraper
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
            if len(inter) == len(keys1) or len(inter) == len(keys2):
                return False
            if len(inter) / len(keys1.union(keys2)) > 0.8:
                return False
        return True
        
    def run(self):
        """
        Code block to run the crawler per each worker
        
        :return: Nothing
        """
        # Initialize containers to check for already visited pages
        list_of_resp = []
        new_visited_links = set()

        while True:
            # Run and grab URLs until Frontier is empty
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            resp = download(tbd_url, self.config, self.logger)

            # Error case for any pages with status codes not = 200
            if resp.status != 200:
                continue

            # Create new Beautiful Soup object if webpage is not empty
            soupt = None
            if resp and resp.raw_response and resp.raw_response.content:
                soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml") 

            # Add to top common words counter for each word
            if resp:
                this_resp = scraper.get_top_common_words(resp, soupt)
                for k,v in this_resp.items():
                    if k in self.most_common_words:
                        self.most_common_words[k] = v +this_resp[k]
                    else:
                        self.most_common_words[k] = v

            # Create parsed url variables to check for unique subdomains
            url_is_parsed = urlparse(resp.url)
            url_is_parsed = url_is_parsed.hostname
            
            # Increment value in unique subdomains for each subdomain
            if "www." in url_is_parsed:
                # Gets rid of the www portion before adding to unique_subdomains
                url_is_parsed = url_is_parsed.split('www.')[1]
            if url_is_parsed in self.unique_subdomains:
                self.unique_subdomains[url_is_parsed] +=1
            else:
                self.unique_subdomains[url_is_parsed] =1

            # Determines if this is the longest webpage found yet
            if self.len_curr_longest_webpage < scraper.get_pg_length(resp, soupt):
                self.curr_longest_webpage = resp.url
                self.len_curr_longest_webpage = scraper.get_pg_length(resp, soupt)

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            # Grab all scraped urls to check for duplicates
            scraped_urls = scraper.scraper(tbd_url, resp, soupt)

            # IN THE CASE IT IS NOT A DUPLICATE, APPEND THE NEW UNIQUE WEBPAGE
            for scraped_url in scraped_urls:
                if scraped_url not in new_visited_links:
                    self.frontier.add_url(scraped_url)
                    new_visited_links.add(scraped_url) 
            
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

        # Print statements to answer Homework 2 question 
        print(f"Length of current longest webpage: {self.len_curr_longest_webpage}")
        print(f"Longest webpage link: {self.curr_longest_webpage}")
        print(f"Most common words: {scraper.top_fifty_words(self.most_common_words)}") 
        print(f"Dictionary of unique subdomain frequency: {self.unique_subdomains}")
