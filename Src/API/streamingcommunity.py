from bs4 import BeautifulSoup
from Src.Utilities.convert import get_TMDb_id_from_IMDb_id
from Src.Utilities.info import get_info_tmdb, is_movie, get_info_imdb
import Src.Utilities.config as config
import json
import random
import re
from urllib.parse import urlparse, parse_qs
from fake_headers import Headers  
from Src.Utilities.loadenv import load_env  
import urllib.parse
User_Agent= "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"

env_vars = load_env()
SC_PROXY = config.SC_PROXY
VX_PROXY = config.VX_PROXY
proxies = {}
proxies2 = {}
if VX_PROXY == "1":
    PROXY_CREDENTIALS = env_vars.get('PROXY_CREDENTIALS')
    proxy_list = json.loads(PROXY_CREDENTIALS)
    proxy = random.choice(proxy_list)
    if proxy == "":
        proxies2 = {}
    else:
        proxies2 = {
            "http": proxy,
            "https": proxy
        }      
if SC_PROXY == "1":
    PROXY_CREDENTIALS = env_vars.get('PROXY_CREDENTIALS')
    proxy_list = json.loads(PROXY_CREDENTIALS)
    proxy = random.choice(proxy_list)
    if proxy == "":
        proxies = {}
    else:
        proxies = {
            "http": proxy,
            "https": proxy
        }   
    if VX_PROXY == "1":
        proxies2 = proxies
 
SC_ForwardProxy = config.SC_ForwardProxy
VX_ForwardProxy = config.VX_ForwardProxy
if SC_ForwardProxy == "1":
    ForwardProxy = env_vars.get('ForwardProxy')
elif VX_ForwardProxy == "1":
    ForwardProxy = env_vars.get('ForwardProxy')
else:
    ForwardProxy = ""
#Get domain
SC_DOMAIN = config.SC_DOMAIN
Public_Instance = config.Public_Instance
Alternative_Link = env_vars.get('ALTERNATIVE_LINK')

headers = Headers()
#GET VERSION OF STREAMING COMMUNITY:
async def get_version(client):
    #Extract the version from the main page of the site


    try:
        random_headers = headers.generate()
        random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
        random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
        base_url = f'https://streamingcommunity.{SC_DOMAIN}/richiedi-un-titolo' 
        response = await client.get(ForwardProxy + base_url, headers=random_headers, allow_redirects = True, impersonate="chrome124", proxies = proxies)
        #Soup the response
        soup = BeautifulSoup(response.text, "lxml")

        # Extract version
        version = json.loads(soup.find("div", {"id": "app"}).get("data-page"))['version']
        return version
    except Exception as e:
        print("Couldn't find the version",e)
        version = "65e52dcf34d64173542cd2dc6b8bb75b"
        return version

async def search(query,date,ismovie, client,SC_FAST_SEARCH,movie_id):
    random_headers = headers.generate()
    random_headers['Referer'] = "https://streamingcommunity.buzz/"
    random_headers['Origin'] = "https://streamingcommunity.buzz"
    random_headers['Accept'] = 'application/json'  # Assuming the API returns JSON
    random_headers['Content-Type'] = 'application/json'
    #Do a request to get the ID of serie/move and it's slug in the URL
    response = await client.get(ForwardProxy + query, headers = random_headers, allow_redirects=True, impersonate = "chrome124", proxies = proxies)
    print(response)
    response = response.json()

    for item in response['data']:
        tid = item['id']
        slug = item['slug']
        type = item['type']
        if type == "tv":
            type = 0
        elif type == "movie":
            type = 1
        if type == ismovie: 
            #Added a Check to see if the result is what it is supposed to be
            if SC_FAST_SEARCH == "0":
                random_headers = headers.generate()
                random_headers['Referer'] = "https://streamingcommunity.buzz/"
                random_headers['Origin'] = "https://streamingcommunity.buzz"
                response = await client.get ( ForwardProxy + f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}', headers = random_headers, allow_redirects=True,impersonate = "chrome124", proxies = proxies)
                soup = BeautifulSoup(response.text, "lxml")
                data = json.loads(soup.find("div", {"id": "app"}).get("data-page"))
                version = data['version']
                if "tt" in movie_id:
                    movie_id = str(await get_TMDb_id_from_IMDb_id(movie_id,client))
                    #Here we need to convert because the IMDB ID is often bugged
                tmdb_id = str(data['props']['title']['tmdb_id'])
                if tmdb_id == movie_id:
                    return tid,slug,version
            elif SC_FAST_SEARCH == "1":
                version = await get_version(client)
                return tid,slug,version
        else:
            print("Couldn't find anything")

        
async def get_film(tid,version,client):  
    random_headers = headers.generate()
    random_headers['Referer'] = "https://streamingcommunity.buzz/"
    random_headers['Origin'] = "https://streamingcommunity.buzz"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    random_headers['User-Agent'] = User_Agent
    random_headers['user-agent'] = User_Agent
    #Access the iframe
    url = f'https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}'
    response = await client.get(ForwardProxy + url, headers=random_headers, allow_redirects=True,impersonate = "chrome124", proxies = proxies)
    iframe = BeautifulSoup(response.text, 'lxml')
    #Get the link of iframe
    iframe = iframe.find('iframe').get("src")
    #Get the ID containted in the src of iframe
    vixid = iframe.split("/embed/")[1].split("?")[0]
    parsed_url = urlparse(iframe)
    query_params = parse_qs(parsed_url.query)
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    random_headers['User-Agent'] = User_Agent
    random_headers['user-agent'] = User_Agent
    #Get real token and expires by looking at the page in the iframe, vixcloud/embed
    resp = await client.get(ForwardProxy + iframe, headers = random_headers, allow_redirects=True,impersonate= "chrome124", proxies = proxies2)
    soup=  BeautifulSoup(resp.text, "lxml")
    script = soup.find("body").find("script").text
    token = re.search(r"'token':\s*'(\w+)'", script).group(1)
    expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
    quality = re.search(r'"quality":(\d+)', script).group(1)
    base_url = re.search(r"url:\s*'(https?://[^']+)'", script).group(1)  
    #Example url  https://vixcloud.co/playlist/231315?b=1&token=bce060eec3dc9d1965a5d258dc78c964&expires=1728995040&rendition=1080p
    url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
    if 'canPlayFHD' in query_params:
       canPlayFHD = 'h=1'
       url += "&h=1"
    if 'b=1' in base_url:
         url += "&b=1"   
    '''   
    if 'b' in query_params:
       b = 'b=1'
       url += "&b=1"
    '''
    '''
    if quality == "1080":
        if "&h" in url:
            url = url
        elif "&b" in url and quality == "1080":
            url = url.replace("&b=1","&h=1")
        elif quality == "1080" and "&b" and "&h" not in url:
            url = url + "&h=1"
    else:
        url = url + f"&token={token}"      
    '''  
    url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
    return url,url720,quality

async def get_season_episode_id(tid,slug,season,episode,version,client):
    random_headers = headers.generate()
    random_headers['Referer'] = "https://streamingcommunity.buzz/"
    random_headers['Origin'] = "https://streamingcommunity.buzz"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    
    #Set some basic headers for the request  
      #Get episode ID 
    response = await client.get(ForwardProxy + f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}/stagione-{season}', headers=random_headers, allow_redirects=True, impersonate = "chrome124", proxies = proxies)
    # Print the json got
    json_response = response.json().get('props', {}).get('loadedSeason', {}).get('episodes', [])
    for dict_episode in json_response:
        if dict_episode['number'] == episode:
            return dict_episode['id']

async def get_episode_link(episode_id,tid,version,client):
    #The parameters for the request
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['User-Agent'] = User_Agent
    random_headers['user-agent'] = User_Agent
    params = {
                'episode_id': episode_id, 
                'next_episode': '1'
            }
    #Let's try to get the link from iframe source
        # Make a request to get iframe source
    response = await client.get(ForwardProxy + f"https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}", params=params, headers = random_headers, allow_redirects=True, impersonate = "chrome124", proxies = proxies)

    # Parse response with BeautifulSoup to get iframe source
    soup = BeautifulSoup(response.text, "lxml")
    iframe = soup.find("iframe").get("src")
    vixid = iframe.split("/embed/")[1].split("?")[0]
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    random_headers['User-Agent'] = User_Agent
    random_headers['user-agent'] = User_Agent
    parsed_url = urlparse(iframe)
    query_params = parse_qs(parsed_url.query)
    #Get real token and expires by looking at the page in the iframe, vixcloud/embed
    resp = await client.get(ForwardProxy + iframe, headers = random_headers, allow_redirects=True, impersonate = "chrome124", proxies = proxies2)
    soup=  BeautifulSoup(resp.text, "lxml")
    script = soup.find("body").find("script").text
    token = re.search(r"'token':\s*'(\w+)'", script).group(1)
    expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
    quality = re.search(r'"quality":(\d+)', script).group(1)
    base_url = re.search(r"url:\s*'(https?://[^']+)'", script).group(1)  

    #Example url  https://vixcloud.co/playlist/231315?b=1&token=bce060eec3dc9d1965a5d258dc78c964&expires=1728995040&rendition=1080p
    url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
    if 'canPlayFHD' in query_params:
       canPlayFHD = 'h=1'
       url += "&h=1"
    if 'b=1' in base_url:
       b = 'b=1'
       url += "&b=1"
    '''
    if quality == "1080":
        if "&h" in url:
            url = url
        elif "&b" in url and quality == "1080":
            url = url.replace("&b=1","&h=1")
        elif quality == "1080" and "&b" and "&h" not in url:
            url = url + "&h=1"
    else:
        url = url + f"&token={token}"
    '''        
    url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
    return url,url720,quality


async def streaming_community(imdb,client,SC_FAST_SEARCH):
    try:
        '''
        if Public_Instance == "1":
            Weird_Link = json.loads(Alternative_Link)
            link_post = random.choice(Weird_Link)
            response = await client.get(f"{link_post}fetch-data/{SC_FAST_SEARCH}/{SC_DOMAIN}/{imdb}")
            url_streaming_community = response.headers.get('x-url-streaming-community')
            url_720_streaming_community = response.headers.get('x-url-720-streaming-community')
            quality_sc = response.headers.get('x-quality-sc')
            print(quality_sc,url_streaming_community)
            return url_streaming_community,url_720_streaming_community,quality_sc
        '''
        general = await is_movie(imdb)
        ismovie = general[0]
        imdb_id = general[1]

        if ismovie == 0 : 
            
            print("MammaMia ismovie = 0")
            season = int(general[2])
            episode = int(general[3])
            #Check if fast search is enabled or disabled
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                if "tt" in imdb:
                #Get showname
                    showname = await get_info_imdb(imdb_id,ismovie,type,client)
                    date = None
                else:
                    #I just set n season to None to avoid bugs, but it is not needed if Fast search is enabled
                    date = None
                    #else just equals them
                    tmdba = imdb_id.replace("tmdb:","")
                    showname = get_info_tmdb(tmdba,ismovie,type)
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                if "tt" in imdb:
                    tmdba = await get_TMDb_id_from_IMDb_id(imdb_id,client)
                showname,date = get_info_tmdb(tmdba,ismovie,type) 
                print("MammaMia found get_info_tmdb")
        #HERE THE CASE IF IT IS A MOVIE
        else:
            print("MammaMia found ismovie=1")
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                if "tt" in imdb:
                    #Get showname
                    date = None
                    showname = await get_info_imdb(imdb_id,ismovie,type,client)
                else:
                        date = None
                        tmdba = imdb_id.replace("tmdb:","")
                        showname = get_info_tmdb(tmdba,ismovie,type) 
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                if "tt" in imdb:
                    #Get showname
                    showname,date = await get_info_imdb(imdb_id,ismovie,type,client)
                else:
                        tmdba = imdb_id.replace("tmdb:","")
                        showname,date = get_info_tmdb(tmdba,ismovie,type) 
        
        showname = showname.replace(" ", "+").replace("–", "+").replace("—","+")
        showname = urllib.parse.quote_plus(showname)
        query = f'https://streamingcommunity.{SC_DOMAIN}/api/search?q={showname}'
        print("MammaMia searching...")
        tid,slug,version = await search(query,date,ismovie,client,SC_FAST_SEARCH,imdb_id)
        print("MammaMia searched")
        if ismovie == 1:
            #TID means temporaly ID
            url,url720,quality = await get_film(tid,version,client)
            print("MammaMia found results for StreamingCommunity")
            return url,url720,quality,slug
        if ismovie == 0:
            #Uid = URL ID
            episode_id = await get_season_episode_id(tid,slug,season,episode,version,client)
            url,url720,quality = await get_episode_link(episode_id,tid,version,client)
            print("MammaMia found results for StreamingCommunity")
            return url,url720,quality,slug
    except Exception as e:
        print("MammaMia: StreamingCommunity failed",e)
        return None,None,None,None

async def test_animeworld():
    from curl_cffi.requests import AsyncSession
    async with AsyncSession() as client:
        # Replace with actual id, for example 'anime_id:episode' format
        test_id = "tt6468322:1:1"  # This is an example ID format
        results = await streaming_community(test_id, client,"0")
        print(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_animeworld())
