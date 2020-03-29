#################################
##### Name: Tianyue Yang
##### Uniqname: tianyuey
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

BASE_URL = 'https://www.nps.gov/index.htm'
CACHE_FNAME = 'cache.json'
CACHE_DICT = {}

headers = {
    'User-Agent': 'UMSI 507 Course Project - Python Scraping',
    'From': 'tianyuey@umich.edu', 
    'Course-Info': 'https://si.umich.edu/programs/courses/507'
}

# SET UP CACHING
def load_cache():
    '''Take content from cache file, called only once when start running the program

    Parameters
    ----------
    None

    Returns
    -------
    dict
        the json object taken from cache file
    '''
    try:
        cache_file = open(CACHE_FNAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    '''Save new changes into cache file, called whenever the cache is changed

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    cache_file = open(CACHE_FNAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''Make webAPI requests using cache if retrieve data from existing cache file

    Parameters
    ----------
    url: string
        url to retrieve data from
    cache: dict
        existing cache dictionary to check content within

    Returns
    -------
    dict
        result dictionary got from making requests and checking cache file
    '''
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


#START DOING THINGS WITH THE NATIONAL SITE
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        """ Get formatted information about the national site

        Parameters
        ----------
        None

        Returns
        -------
        str
            formatted information about the national site
        """
        #EXAMPLE: Isle Royale (National Park): Houghton, MI 49931
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    #Make the soup
    response = make_url_request_using_cache(BASE_URL, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    state_url_dict = {}
    states = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    
    list_states = states.find_all('li', recursive=False)

    for s in list_states:
        name = s.find('a').text.strip().lower() #state name
        url = s.find('a')['href'] #state url
        state_url_dict[name] = 'https://www.nps.gov' + url

    return state_url_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    #Things to get: category, name, address, zipcode, phone
    #EXAMPLE: Isle Royale (National Park): Houghton, MI 49931  
    category = soup.find('span', class_='Hero-designation').text.strip()
    name = soup.find('a', class_='Hero-title').text.strip()
    locality = soup.find('span', attrs={'itemprop': 'addressLocality'}).text.strip()
    region = soup.find('span', attrs={'itemprop': 'addressRegion'}).text.strip()
    address = locality + ', ' + region
    zipcode = soup.find('span', attrs={'itemprop': 'postalCode'}).text.strip()
    phone = soup.find('span', attrs={'itemprop': 'telephone'}).text.strip()
    site = NationalSite(category, name, address, zipcode, phone)
    return site
     


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    response = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    sites = []
    sites_parent = soup.find('ul', id='list_parks')
    sites_child = sites_parent.find_all('li', recursive=False)
    for child in sites_child:
        path = child.find('a')['href']
        site_url = 'https://www.nps.gov/' + path + 'index.htm'
        site_instance = get_site_instance(site_url)
        sites.append(site_instance)
    return sites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    resource_url = 'http://www.mapquestapi.com/search/v2/radius?'
    search_attr = f'origin={site_object.zipcode}&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json&key={secrets.API_KEY}'
    search_url = resource_url + search_attr
    response = make_url_request_using_cache(search_url, CACHE_DICT)
    data = json.loads(response)
    return data

#GET A LIST OF STATES
states = []
initial_response = requests.get(BASE_URL).text
soup = BeautifulSoup(initial_response, 'html.parser')

states_parent = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
states_child = states_parent.find_all('li', recursive=False)
for child in states_child:
    state = child.find('a').text.strip().lower()
    states.append(state)
#print(states)

#IMPLEMENTING AN INTERACTIVE SEARCH SYSTEM
if __name__ == "__main__":
    CACHE_DICT = load_cache()
    get_response = input('Enter a state name (e.g. Michigan, michigan) or \"exit\"\n: ')
    get_response = str(get_response)
    while get_response.lower() != 'exit':
        if get_response.lower() not in states:
            print('[Error] Enter proper state name')
            get_response = input('Enter a state name (e.g. Michigan, michigan) or \"exit\"\n: ')
        else:
            state_input = get_response.lower()
            states_url_dict = build_state_url_dict()
            state_url = states_url_dict[state_input]
            sites_for_state = get_sites_for_state(state_url)
            print('-------------------------------------------')
            print(f'List of national sites in {state_input}')
            print('-------------------------------------------')
            start_number = 1
            for site in sites_for_state:
                print(f'[{start_number}] {site.info()}')
                start_number += 1

            #LET USER SEARCH FOR MORE BY PICKING A NUMBER
            get_number = input('Choose the number for detail search or \"exit\" or \"back\"\n: ')
            get_number = get_number.lower()
            while get_number != 'exit':
                try:
                    get_number = int(get_number)
                    if get_number not in range(len(sites_for_state)+1):
                        print('[Error] Invalid Input')
                        print('-------------------------------------------')
                        get_number = input('Choose the number for detail search or \"exit\" or \"back\"\n: ')
                except:
                    print('[Error] Invalid Input')
                    print('-------------------------------------------')
                    get_number = input('Choose the number for detail search or \"exit\" or \"back\"\n: ')
                if get_number in range(len(sites_for_state)+1):
                    get_indice = int(get_number) - 1
                    get_site = sites_for_state[get_indice]
                    get_places = get_nearby_places(get_site)['searchResults']
                    print('-------------------------------------------')
                    print(f'Places near {get_site.name}')
                    print('-------------------------------------------')
                    #EXAMPLE: - <name> (<category>): <street address>, <city name>
                    for item in get_places:
                        place_name = item['name']
                        if 'group_sic_code_name' in item['fields'].keys():
                            if item['fields']['group_sic_code_name'] != '':
                                place_category = item['fields']['group_sic_code_name']
                            else:
                                place_category = 'no category'
                        else:
                            place_category = 'no category'
                        if 'address' in item.keys():
                            if item['address'] != '':
                                place_address = item['address']
                            else:
                                place_address = 'no address'
                        else:
                            place_address = 'no address'
                        if 'city' in item['fields'].keys():
                            if item['fields']['city'] != '':
                                place_city = item['fields']['city']
                            else:
                                place_city = 'no city'
                        else:
                            place_city = 'no city'

                        print(f'- {place_name} ({place_category}): {place_address}, {place_city}')

                    get_number = input('Choose the number for detail search or \"exit\" or \"back\"\n: ')
                    
                if get_number == 'back':
                    get_response = input('Enter a state name (e.g. Michigan, michigan) or \"exit\"\n: ')
                    break

            else:
                exit()
    else:
        exit()

                        

    

                        
                            
            
