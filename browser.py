import time
import json
import typing
import requests
import contextlib
import undetected_chromedriver
import selenium.webdriver.support.wait

def fetch(browser: undetected_chromedriver.Chrome, url: str) -> None:
    '''
    Fetches a HTML page.
    '''
    
    print(f'[ BROWSER ] Navigating to {url}')
    browser.get(url)
    
    print('[ BROWSER ] Waiting for human to exit IUAM')
    selenium.webdriver.support.wait.WebDriverWait(browser, 180).until(
        lambda b: '<title>Just a moment...' not in b.page_source
    )
    
    print('[ BROWSER ] Filtering requests')
    # NOTE - We use the chrome dev console because some of the Japscan
    # data is erased on page load.
    
    for log in browser.get_log('performance'):
        data = json.loads(log['message'])['message']
        
        # Filter entry
        if (
            data['method'] != 'Network.responseReceived'
            or data['params']['type'] != 'Document'
            or data['params']['response']['status'] != 200
            or data['params']['response']['url'].strip('/') != url.strip('/')
            or not 'text/html' in data['params']['response']['mimeType']
        ):
            continue
        
        id = data['params']['requestId']
        print(f'[ BROWSER ] Extracting request {id}')
        
        # Get response body
        return browser.execute_cdp_cmd('Network.getResponseBody', {
            'requestId': id
        })['body']
    
    raise Exception('Failed to find request body log')

@contextlib.contextmanager
def Chrome() -> typing.Iterator[undetected_chromedriver.Chrome]:
    '''
    Initialise a UC browser.
    '''
    
    print('[ BROWSER ] Creating browser')
    
    options = undetected_chromedriver.ChromeOptions()
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-browser-side-navigation')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    browser = undetected_chromedriver.Chrome(options)
    browser.fetch = lambda url: fetch(browser, url)
    
    try:
        yield browser
    
    finally:
        print('[ BROWSER ] Closing browser peacefully')
        browser.close()

def request(method: str,
            url: str,
            data: typing.Any = None,
            timeout: float = 10) -> requests.Response:
    '''
    Makes HTTP requests with a retry mechanism.
    '''
    
    while 1:
        response = requests.request(method, url, data = data)
        
        if response.status_code == 429:
            print(f'[ REQUEST ] API is overloaded, waiting {timeout}s')
            time.sleep(timeout)
            continue
        
        if not response.ok:
            print(f'[ REQUEST ] API error {response.status_code}: {response.text}')
            exit(1)
        
        return response

# EOF