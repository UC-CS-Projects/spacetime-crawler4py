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
        self.curr_longest_webpage = ''
        self.len_curr_longest_webpage = 0
        self.most_common_words = {}
        self.unique_subdomains = {}
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
            if len(inter) / len(keys1.union(keys2)) > 0.8:
                return False
            #if len(inter) > 1000:
            #    return False #false means this url is essentially a duplicate webpage
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

            if resp:# and resp.status == 200 and resp.raw_response:
                this_resp = scraper.get_top_common_words(resp)
                for k,v in this_resp.items():
                    if k in self.most_common_words:
                        self.most_common_words[k] = v +this_resp[k]

#                    self.most_common_words.update() #add the new scraped words to the global dictionary variable


            url_is_parsed = urlparse(resp.url)
            url_is_parsed = url_is_parsed.hostname
            if url_is_parsed in self.unique_subdomains:
                self.unique_subdomains[url_is_parsed] +=1
            else:
                self.unique_subdomains[url_is_parsed] =1

                    
            if self.len_curr_longest_webpage < scraper.get_pg_length(resp):
                self.curr_longest_webpage = resp.url
                self.len_curr_longest_webpage = scraper.get_pg_length(resp)

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            #if scraper.robots_text_file(tbd_url, valid_domains, self.config, self.logger):
            #print("before scraper")
            scraped_urls = scraper.scraper(tbd_url, resp)
            #print("after scraper")

            #if self.find_intersection(list_of_resp, resp): #call find_intersection to detect duplicate webpages
                #list_of_resp.append(resp) #IN THE CASE IT IS NOT A DUPLICATE, APPEND THE NEW UNIQUE WEBPAGE
            for scraped_url in scraped_urls:
                if scraped_url not in new_visited_links:
                    self.frontier.add_url(scraped_url)
                    new_visited_links.add(scraped_url) #should handle infinite traps. does not account for session IDs and URL
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        print(scraper.top_fifty_words(self.most_common_words)) #prints the top 50 list of all the words from most frequent to least frequent

        print(self.unique_subdomains)
