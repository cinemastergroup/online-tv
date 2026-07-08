import sys
import os
import re
import datetime
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import requests

BASE_URL = "https://cinemastergroup.github.io/online-tv/"
HANDLE = int(sys.argv[1])

def get_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=10)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def resolve_ok_ru(embed_url):
    """Kiharássza az OK.ru iframe-ből a közvetlen MP4 videó linket."""
    html = get_html(embed_url)
    if not html: return None
    match = re.search(r'data-options="([^"]+)"', html)
    if match:
        decoded = urllib.parse.unquote(match.group(1))
        links = re.findall(r'"url"\s*:\s*"([^"]+)"', decoded)
        if links:
            return links[-1].replace(r'\/', '/')
    return None

def resolve_archive_org(embed_url):
    """Visszafejti a beágyazott Archive.org linkből a nyers MP4-et."""
    html = get_html(embed_url)
    match = re.search(r'<source\s+src="([^"]+\.mp4)"', html)
    if match:
        url = match.group(1)
        if url.startswith('//'): url = 'https:' + url
        return url
    return None

def list_channels():
    """Megjeleníti a csatornaválasztó menüt a Kodiban."""
    channels = [
        {"id": "cinemaster", "name": "CineMaster"},
        {"id": "cinemaster2", "name": "CineMaster 2"},
        {"id": "retrotv", "name": "RetroTV"},
        {"id": "besthits", "name": "Best Hits TV"}
    ]
    
    for ch in channels:
        list_item = xbmcgui.ListItem(label=ch['name'])
        # Beállítjuk a csatorna alapértelmezett logóját a GitHub-ról
        list_item.setArt({'thumb': f"{BASE_URL}logos/{ch['id']}.png"})
        
        url = f"{sys.argv[0]}?action=play&channel={ch['id']}"
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
        
    xbmcplugin.endOfDirectory(HANDLE)

def play_channel(channel_id):
    """Kiszámolja a helyi idő szerinti aktuális műsort és elindítja a lejátszást."""
    # A te rendszered a helyi (magyar) időzónát követi, így a tiszta helyi időt vesszük alapul
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    schedule_url = f"{BASE_URL}{channel_id}_schedule_{date_str}.json"
    
    try:
        r = requests.get(schedule_url, timeout=5)
        if r.status_code != 200:
            xbmcgui.Dialog().notification("CineMaster", "Nem érhető el az adásmenet!", xbmcgui.NOTIFICATION_ERROR)
            return
        data = r.json()
    except:
        return

    current_track = None
    for track in data.get('schedule', []):
        start_time = datetime.datetime.strptime(track['start'], "%Y-%m-%dT%H:%M:%S")
        end_time = start_time + datetime.timedelta(seconds=track['duration'])
        
        if start_time <= now < end_time:
            current_track = track
            break

    if not current_track:
        xbmcgui.Dialog().notification("CineMaster", "Jelenleg nincs adás ezen a csatornán.", xbmcgui.NOTIFICATION_INFO)
        return

    embed_url = current_track['url']
    video_url = None
    
    # URL feloldása forrás alapján
    if "ok.ru" in embed_url:
        video_url = resolve_ok_ru(embed_url)
    elif "archive.org" in embed_url:
        video_url = resolve_archive_org(embed_url)

    if not video_url:
        xbmcgui.Dialog().notification("CineMaster", "Nem sikerült feloldani a videó forrást.", xbmcgui.NOTIFICATION_ERROR)
        return

    # Kiszámoljuk a másodpercre pontos indítási pozíciót (StartOffset)
    seconds_in = int((now - start_time).total_seconds())
    if seconds_in < 0: seconds_in = 0

    list_item = xbmcgui.ListItem(label=current_track['title'])
    list_item.setProperty('StartOffset', str(seconds_in))

    # Átadjuk a kész, feloldott MP4 URL-t a Kodinak lejátszásra
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=list_item)
    xbmc.Player().play(item=video_url, listitem=list_item)

# Router logika
params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
action = params.get('action')

if action == 'play':
    play_channel(params.get('channel'))
else:
    list_channels()
