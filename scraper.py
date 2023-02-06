import re, lxml, nltk
nltk.download('punkt')
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from urllib.parse import urlparse
from utils.download import download
import urllib.robotparser
import chardet

def scraper(url, resp, soupt):
    """
    Scrapes through links using baseline url

    :param url: Starting url to begin crawling
    :param resp: Response from downloading website
    :return: List of links if they are valid (check is_valid for requirements)
    """
    links = extract_next_links(url, resp, soupt)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp, soupt):
    """
    Extracts hyperlinks from each page and returns a list of hyperlinks

    :param url: Starting url to begin crawling
    :param resp: Response from downloading website
        resp.url: the actual url of the page
        resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
        resp.error: when status is not 200, you can check the error here, if needed.
        resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
            resp.raw_response.url: the url, again
            resp.raw_response.content: the content of the page!
    :param soupt: Beautiful Soup object 
    :return: List with hyperlinks (str) scrapped from resp.raw_response.content
    """
    # Error case for any pages with status code != 200
    if resp.status != 200 or not soupt:
        # Print error and return empty list --> no hyperlinks extracted
        print(resp.error) 
        return list()

    # Call tokenize function to get all the valuable words on the webpage, as a list
    no_stop_words = cust_tokenize(soupt) 

    # Create list and set objects to store hyperlinks : nonunqiue, unique
    hyperlink_list = list()
    visited_set = set()

    # Store unparsed href and # of headings --> determines information value of page
    unparsed_href_list = soupt.find_all("a")

    # Our definition of low-info value webpage:
        #under 100 words AND no headings AND less than 2 hyperlinks
    if (len(no_stop_words) < 100 and len(unparsed_href_list) < 2) or (len(resp.raw_response.content) < 500):
        # Printing out specifics of page that led to error, return empty list
        print("Page is low information value")
        print(f"Number of non-stop words: {len(no_stop_words)}")
        print(f"Length of unparsed hrefs: {len(unparsed_href_list)} | Length of raw_response content: {len(resp.raw_response.content)}")
        return list()

    # Go through soupt href list, get only hyperlinks 
    for link in unparsed_href_list:
        web_url_string = link.get('href')

        # Keep looping until hyperlink is found
        if not web_url_string:
            continue

        # Grab url and check if it has not been visited    
        defrag_url = web_url_string.split("#")[0]
        if defrag_url.strip() == "" or "id=" in defrag_url:
            continue
        #if defrag_url not in visited_set:
            # Parse URL and get rid of URL fragment
        parsed = urlparse(defrag_url)
            #new link we scraped
        orginal_website = urlparse(resp.url)

        if parsed.scheme.strip() == "":
            if parsed.netloc != "": #"//www.google.com"
                new_absolute_link = parsed._replace(fragment="").geturl()
                new_absolute_link = new_absolute_link[2:]
                new_scraped_link = "http://"+ new_absolute_link
            else:
                if len(parsed.path) >2 and "." == parsed.path[0]: # "./ugrad/academia or ugrad/academia"

                    #Relative path
                    #while loop
                        #counter
                        #while "../" and correct length >3 ) or "./" and correct length >2
                    #print("defrag: ", defrag_url)
                    counter_path = 0
                    current_path = orginal_website.path

                        #parsed/defrag/new_url path
                    new_path = parsed.path
                    while True:
                        if (len(new_path) > 2 and "../" == new_path[:3]):
                            counter_path += 2
                            new_path = new_path[3:]
                        elif (len(new_path) >1 and "./" == new_path[:2]):
                            #counter_path += 1
                            new_path = new_path[2:]
                        else:
                            break
                    current_path_splitted = current_path.split("/")
                    for i in range(counter_path):
                        if len(current_path_splitted) > 0:
                            current_path_splitted.pop()
                        else:
                            break
                    new_realtive_link = orginal_website._replace(path= "/".join(current_path_splitted)+ "/"+new_path).geturl()
                    new_scraped_link = new_realtive_link
                    #print("new_realtive_link: ", new_realtive_link)

                else:
                        # "/ugrad"
                        #Absoulte path
                    orginal_website = orginal_website._replace(path = parsed.path)
                    orginal_website = orginal_website._replace(fragment="")
                    orginal_website = orginal_website._replace(params = "")
                    new_absolute_link = orginal_website._replace(query ="").geturl()
                    new_scraped_link = new_absolute_link
        else:
                #print("norm")
                # Append to list/set for checking if hyperlink exists in future iterations            
            new_scraped_link = defrag_url

        
        if new_scraped_link not in visited_set:
            hyperlink_list.append(new_scraped_link)
            visited_set.add(new_scraped_link)


    return hyperlink_list

def is_valid(url):
    """
    Determine whether to crawl URL or not
    Returns True if crawl, else False

    :param url: URL to check if valid
    :return: True or False if valid
    """   
    valid_domain_names = [".stat.uci.edu/", ".ics.uci.edu/", ".cs.uci.edu/", ".informatics.uci.edu/"]
    
    # Try/Except in case parsed value is not of correct type --> raises error
    try:
        # Parse url and get specific parts 
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check if parsed domain is valid and add to container 
        in_domain = []
        for i in valid_domain_names:
            in_domain.append(i in parsed.geturl())

        # If domain list empty, return False 
        if not any(in_domain):
            return False
            
        # Prevents infinite loops in Calendar sites through regex by not crawling specific dates/events
        if ('wics.ics.uci.edu/events/' in url) or ('page' in url) or ('wp-json' in parsed.path) or ('pdf' in parsed.path) or ('ical=' in parsed.query) or ('share=' in parsed.query) or ('id=' in parsed.query):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def cust_tokenize(soupt):
    """
    Receives resp object and returns only non-stop words in website

    :param soupt: Beautiful Soup object
    :return: List of non-stop words
    """
    if not soupt:
        return []

    # Stop words list gathered from Assignment 2 page
    stops = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']
   
    # Retrieve text from page
    raw_text = soupt.get_text() 
    
    # Use NLTK to tokenize into list & get text
    # Code referenced from -> https://www.bogotobogo.com/python/Flask/Python_Flask_App_2_BeautifulSoup_NLTK_Gunicorn_PM2_Apache.php
    tokens = nltk.word_tokenize(raw_text)
    text = nltk.Text(tokens) 
    nonPunct = re.compile('.*[A-Za-z].*') 

    # List of every single word without punctuation on the webpage, including stop words
    raw_words = [w for w in text if nonPunct.match(w)] 

    # List of high-value words excluding common, nondescriptive words (conjunctions)
    no_stop_words = [w for w in raw_words if w.lower() not in stops]
    return no_stop_words

def get_pg_length (resp, soupt):
    """
    Retrieve page length from resp

    :param resp: Response from downloading website
    :param soupt: Beautiful Soup object
    :return: Length of page
    """
    # Type checking to ensure page is valid
    if not soupt:
        return 0
    if not resp or not resp.raw_response or  not resp.raw_response.content:
        return 0

    # Grabs all text -> tokenizes and adds to list
    raw_text = soupt.get_text() 
    tokens = nltk.word_tokenize(raw_text) 
    return len(tokens)

def get_top_common_words(resp,soupt):
    """
    Grabs all words and returns a dictionary of the most common tokens

    :param resp: Response from downloading website
    :param soupt: Beautiful Soup object
    :return: Dictionary of words with frequencies
    """
    dicta = {}

    # Type checking to ensure page is valid
    if not resp or not resp.raw_response or  not resp.raw_response.content:
        return dicta

    # Tokenizes to only get non-stop words
    no_stop_words = cust_tokenize(soupt)
    
    # Iterates through tokens, increments dictionary key pair value by 1 
    for tok in no_stop_words:
        if tok not in dicta:
            dicta[tok.lower()] = 1
        else:
            dicta[tok.lower()] += 1
    return dicta

def top_fifty_words(freq):
    """
    Sorted words by frequency and returns the top 50

    :param freq: Frequency of words via dictionary
    :return: Sorted container with 50 values
    """
    allTokens = sorted(freq.items(), key = lambda x: (x[1], x[0]), reverse = True)
    return allTokens[:50]