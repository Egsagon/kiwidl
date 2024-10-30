import browser
import zipfile

# Settings
API = 'https://webtoon.cloud'
URL = '< JAPSCAN INPUT CHAPTER URL >'
OUT = '< OUTPUT PATH TO CBZ >'

print(f'[ SCRAPER ] harvesting {URL}')

try:
    with browser.Chrome() as chrome:
        page = chrome.fetch(URL)

except Exception as err:
    print(f'[ SCRAPER ] {err.__class__.__name__}: {str(err)}')
    exit(1)

print('[ SCRAPER ] Sending page for API to process')

images = browser.request('POST', API + '/pages', data = page, timeout = 60).json()

print(f'[ SCRAPER ] Received {len(images)} from API')

with zipfile.ZipFile(OUT, 'w') as archive:
    for i, uri in enumerate(images, start = 1):
        
        print(f'[ SCRAPER ] Downloading image {i}/{len(images)}: {uri}')
        response = browser.request('GET', API + uri, timeout = 5)
        archive.writestr(f'{i}.{uri.split(".")[-1]}', response.content)
        
        # Don't trigger API rate limit
        browser.time.sleep(.6)

print(f'[ SCRAPER ] Download complete: {OUT}')

# EOF
