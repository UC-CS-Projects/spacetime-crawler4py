import re, lxml, nltk
nltk.download('punkt')
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils.download import download
import urllib.robotparser



def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200:
        # Error case for any pages with status codes not = 200
        print(resp.error) 
        return list()
    

    #soupt = BeautifulSoup(resp.raw_response.content, "lxml") #create beautiful soup object
    soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml") #create beautiful soup object

    no_stop_words = cust_tokenize(resp) #call tokenize function to get all the valuable words on the webpage, as a list

    # Create list and set objects to store hyperlinks : nonunqiue, unique
    hyperlink_list = list()
    visited_set = set()

    # Example soupt value -> [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>]
    unparsed_href_list = soupt.find_all("a")
    num_of_headings = soupt.find_all(["h1", "h2", "h3"])
    #our definition of a webpage with low information value would be:
        #under 100 words AND no headings AND less than 2 hyperlinks
    if (len(no_stop_words) < 100 and len(num_of_headings) == 0 and len(unparsed_href_list) < 2) or (len(resp.raw_response.content) < 500): #checking if the page is a low value information page
        print("page is low information value")
        return list()

    #go through soupt list, get only hyperlinks 
    for link in unparsed_href_list:
        web_url_string = link.get('href')
        if not web_url_string:
            continue
        defrag_url = web_url_string.split("#")[0]
        if defrag_url not in visited_set:
            parsed = urlparse(defrag_url)
            parsed._replace(fragment="").geturl #getting rid of the fragment of the URL
            hyperlink_list.append(defrag_url)
            visited_set.add(defrag_url)

    return hyperlink_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    valid_domain_names = [".ics.uci.edu/", ".cs.uci.edu/", ".informatics.uci.edu/", ".stat.uci.edu/"]
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        #check if domain is correct
        in_domain = []
        for i in valid_domain_names:
            #print(parsed.hostname)
            in_domain.append(i in parsed.geturl())

        if not any(in_domain):
            #print(url, in_domain)
            return False


        #Check if adhears to robot.txt file 
        try:
            rp = urllib.robotparser.RobotFileParser()
            robot_url = parsed.scheme+ "://"+ parsed.hostname + '/robots.txt'
            rp.set_url(robot_url)
            rp.read()
            #If true than keep validating
            if not rp.can_fetch("*", parsed.geturl()):
                return False
        except:
            pass


        #parsed._replace(fragment="").geturl #getting rid of the fragment of the URL
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

def cust_tokenize(resp):
    #stop words list from https://www.bogotobogo.com/python/Flask/Python_Flask_App_2_BeautifulSoup_NLTK_Gunicorn_PM2_Apache.php
    stops = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you','your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his','himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself','they', 'them', 'their', 'theirs', 'themselves', 'what', 'which','who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are','was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having','do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if','or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for','with', 'about', 'against', 'between', 'into', 'through', 'during','before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in','out', 'on', 'off', 'over', 'under', 'again', 'further', 'then','once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any','both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no','nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's','t', 'can', 'will', 'just', 'don', 'should', 'now', 'id', 'var','function', 'js', 'd', 'script', '\'script', 'fjs', 'document', 'r','b', 'g', 'e', '\'s', 'c', 'f', 'h', 'l', 'k']
    soupt = BeautifulSoup(resp.raw_response.content.decode('utf-8', 'ignore'), "lxml") #create beautiful soup object
    raw_text = soupt.get_text() #gets all the text from the url, returns a string
    tokens = nltk.word_tokenize(raw_text) #get all the tokens from the raw_text string, returns a list
    text = nltk.Text(tokens) #code from line 32-35 from https://www.bogotobogo.com/python/Flask/Python_Flask_App_2_BeautifulSoup_NLTK_Gunicorn_PM2_Apache.php
    nonPunct = re.compile('.*[A-Za-z].*') 
    raw_words = [w for w in text if nonPunct.match(w)] #list of every single word without punctuation on the webpage
    no_stop_words = [w for w in raw_words if w.lower() not in stops] #list of high-value words excluding common, nondescriptive words (conjunctions)
    return no_stop_words


def robots_text_file(url, domains, config, logger) -> bool:

    parsed = urlparse(url)
    dom = parsed.hostname
    if dom in domains:
        print("indomain")
        _,disallows, entire_domain = domains[dom]
        if not entire_domain:
            return False#IF there is a "/" we would be disallowed on the entire subdomain

        for i in disallows:
            if i in parsed.geturl():
                return False# there is a disallowed website

        return True
        
    else:
        rp = urllib.robotparser.RobotFileParser()
        robot_url = "https://"+ parsed.hostname + '/robots.txt'

        rp.set_url(robot_url)
        rp.read()
    
        #roblox = download(robot_url, config, logger)

#        if roblox.status != 200:
#            return True
        
        #parsed_roblox = BeautifulSoup(roblox.raw_response.content.decode('utf-8', 'ignore'), "lxml")
        #print(parsed_roblox)
        #roblox_txt = parsed_roblox.get_text() #returns /robot.txt as a string
        #print(roblox_txt)
        #roblox_splitted = roblox_txt.splitlines()
        #print(roblox_splitted)
        return True

    #Parse the url. grab the hostname/domain-  check if its in the valid domain
        #if it's not
            #add the new subdomain into the unique subdomain list.
            #determine if robots.txt file exist
                #Parse if it it does. Adding all of the disallows and sitemaps respectively
                #check if / is in disallow, change respectivly value
                #Validate
            #not continue
        #It is.
            #Validate

        #Validate
            #check if allowed to go in website
            #check all disallowed list against url. contuine or don't contunie
    
    pass