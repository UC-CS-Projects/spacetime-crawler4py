import re, lxml, nltk
nltk.download('punkt')
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils.download import download
import urllib.robotparser
from collections import defaultdict

def scraper(url, resp):
    """
    Scrapes through links using baseline url

    :param url: Starting url to begin crawling
    :param resp: Response from downloading website
    :return: List of links if they are valid (check is_valid for requirements)
    """
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
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
    :return: List with hyperlinks (str) scrapped from resp.raw_response.content
    """
    # Error case for any pages with status code != 200
    if resp.status != 200:
        # Print error and return empty list --> no hyperlinks extracted
        print(resp.error) 
        return list()

    # Create beautiful soup object - helps to parse html file
    # Example soupt value -> [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>]
    soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml")

    # Call tokenize function to get all the valuable words on the webpage, as a list
    no_stop_words = cust_tokenize(resp) 

    # Create list and set objects to store hyperlinks : nonunqiue, unique
    hyperlink_list = list()
    visited_set = set()

    # Store unparsed href and # of headings --> determines information value of page
    unparsed_href_list = soupt.find_all("a")
    num_of_headings = soupt.find_all(["h1", "h2", "h3"])

    # Our definition of low-info value webpage:
        # Under 100 non-stop words AND no headings AND less than 2 hyperlinks OR raw_content < 500 words
    if (len(no_stop_words) < 100 and len(num_of_headings) == 0 and len(unparsed_href_list) < 2) or (len(resp.raw_response.content) < 500): 
        # Printing out specifics of page that led to error, return empty list
        print("Page is low information value")
        print(f"Number of non-stop words: {len(no_stop_words)} | Number of headings: {len(num_of_headings)}")
        print(f"Length of unparsed hrefs: {len(unparsed_href_list)} | Length of raw_response content: {len(resp,raw_response.content)}")
        return list()

    # Go through soupt href list, get only hyperlinks 
    for link in unparsed_href_list:
        web_url_string = link.get('href')

        # Keep looping until hyperlink is found
        if not web_url_string:
            continue
        
        # Grab url and check if it has not been visited
        defrag_url = web_url_string.split("#")[0]
        if defrag_url not in visited_set:
            # Parse URL and get rid of URL fragment
            parsed = urlparse(defrag_url)
            parsed._replace(fragment="").geturl 

            # Append to list/set for checking if hyperlink exists in future iterations
            hyperlink_list.append(defrag_url)
            visited_set.add(defrag_url)

    return hyperlink_list

def is_valid(url):
    """
    Determine whether to crawl URL or not

    Returns True if crawl, else False

    :param url: URL to check if valid
    :return: True or False if valid
    """

    valid_domain_names = [".ics.uci.edu/", ".cs.uci.edu/", ".stat.uci.edu/", ".informatics.uci.edu/"]
   
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

        # Try/Except to check if robot.txt file rules are followed -> passes if not, ignores txt file
        try:
            robot_txt_url = parsed.scheme+ "://"+ parsed.hostname + '/robots.txt'

            # Create Robot File Parser object and read robot file
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robot_txt_url)
            rp.read()

            # If True, continue validating 
            if not rp.can_fetch("*", parsed.geturl()):
                return False  
        except:
            pass

        # Prevents infinite loops in Calendar sites through regex by not crawling specific dates/events
        if re.search('^.events.$', url) or re.search('^.event.$', url) or re.search('^.calendar.$', url):
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
        print ("TypeError for: ", parsed)
        raise 

def cust_tokenize(resp):
    """
    Receives resp object and returns only non-stop words in website

    :param resp: Response from downloading website
    :return: List of non-stop words
    """
    # Stop words list gathered from Assignment 2 page
    stops = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']
    
    # Create BeautifulSoup object and retrieve all text from page
    soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml") 
    raw_text = soupt.get_text() 

    # Use NLTK to tokenize into list & get text
    # Code referenced from -> https://www.bogotobogo.com/python/Flask/Python_Flask_App_2_BeautifulSoup_NLTK_Gunicorn_PM2_Apache.php
    tokens = nltk.word_tokenize(raw_text) 
    text = nltk.Text(tokens) 

    nonPunct = re.compile('.*[A-Za-z].*') 
    # List of every single word without punctuation on the webpage, including stop words
    raw_words = [w for w in text if nonPunct.match(w)] 
    
    # List of high-value words excluding common, nondescriptive words (conjunctions)
    no_stop_words = [word for word in raw_words if word.lower() not in stop_words] 
   
    return no_stop_words

def get_pg_length (resp):
    """
    Retrieve page length from resp

    :param resp: Response from downloading website
    :return: Length of page
    """
    print("Page length (get_pg_len): ", resp)
    # Create beautiful soup object
    soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml") 

    #Grabs all text -> tokenizes and adds to list
    raw_text = soupt.get_text() 
    tokens = nltk.word_tokenize(raw_text) 
    return len(tokens)

def get_top_common_words(resp):
    """
    Grabs all words and returns a dictionary of the most common tokens

    :param resp: Response from downloading website
    :return: Dictionary of words with frequencies
    """
    word_frequencies = defaultdict(int)

    # Tokenizes to only get non-stop words
    no_stop_words = cust_tokenize(resp)
    
    # Tokens is the list of all the words on the page
    tokens = nltk.word_tokenize(no_stop_words) #get all the tokens from the raw_text string, returns a list

    # Iterates through tokens, increments dictionary key pair value by 1 
    for token in tokens:
        word_frequencies[token.lower()] += 1
    
    return word_frequencies

def top_fifty_words(freq):
    allTokens = sorted(freq.items(), key = lambda x: (x[1], -x[0]), reverse = True)
    return allTokens[:50]