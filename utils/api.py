from .logger import logger
from .types import Release

import aiohttp
import bs4


VALID_RELEASES = (
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'watchOS'
)

async def rss(url: str):
    if url.startswith('/'):
        f = open(url, 'r')
        r = f.read()
    else:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    r = await resp.text()
        except Exception:
            logger.error('Error fetching the URL: ', url)
    try:    
        soup = bs4.BeautifulSoup(r, features='html.parser')
    except Exception:
        logger.error('Could not parse the xml: ', url)
    articles = [{'title':a.find('title').text,'link':a.link.next_sibling.replace('\n','').replace('\t',''),'description':a.find('description').text,'pubdate':a.find('pubdate').text} for a in soup.findAll('item')]
    return articles

def format_feed(feed: list) -> list:
    """Formats recieved RSS entries into an interable list of Release objects.
    
    Args:
        feed (list): List of RSS entries.
    Returns:
        
    """
    # Introduce needed variables
    releases = []
    # Iterate through items in feed
    for item in feed:
        if item.get('title').split()[0] in VALID_RELEASES:
            releases.append(Release(item))
    # Return what we found
    return releases

async def fetch_firmwares() -> list:
    """Fetches all (recently) released firmwares.
    
    Returns:
        List of recently released firmwares.
    """
    # Return releases
    return format_feed(await rss('https://developer.apple.com/news/releases/rss/releases.rss'))

async def compare_firmwares(to_compare: list) -> list:
    """Compares already fetched firmware list to the current firmwares.
    
    Args:
        to_compare (dict): Dictionary object of firmwares.
    Returns:
        Firmwares in recent list that weren't in previous.
    """
    # Get all firmwares from the API
    firmwares = await fetch_firmwares()
    # Compare new firmwares to old firmwares
    differences = []
    for firmware in firmwares:
        # Check if the firmware is new
        if firmware not in to_compare:
            # Add the new firmware to the list of differences
            differences.append(firmware)
    # Return the differences
    return differences