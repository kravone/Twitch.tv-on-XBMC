import sys
import urllib2
import urllib
import re
import xbmcaddon
import os
import socket
try:
    import json
except:
    import simplejson as json
from xbmcswift2 import Plugin

settings = xbmcaddon.Addon(id='plugin.video.twitch')
httpHeaderUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
translation = settings.getLocalizedString
ITEMS_PER_SITE = 20

plugin = Plugin()


def downloadWebData(url):
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', httpHeaderUserAgent)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.HTTPError, e:
        # HTTP errors usualy contain error information in JSON Format
        return e.fp.read()
    except urllib2.URLError, e:
        xbmc.executebuiltin("XBMC.Notification(" + translation(
            32001) + "," + translation(32010) + ")")


def getJsonFromTwitchApi(url):
    jsonString = downloadWebData(url)
    if jsonString is None:
        return None
    try:
        jsonData = json.loads(jsonString)
    except:
        xbmc.executebuiltin('XBMC.Notification("' + translation(
            32008) + '","' + translation(32008) + '")')
        return None
    if type(jsonData) is dict and 'error' in jsonData.keys():
        xbmc.executebuiltin('XBMC.Notification("' + translation(
            32007) + '","' + jsonData['error'] + '")')
        return None
    return jsonData


@plugin.route('/')
def createMainListing():
    items = [
        {'label': translation(30005), 'path': plugin.url_for(
            endpoint='createListOfFeaturedStreams'
        )},
        {'label': translation(30001), 'path': plugin.url_for(
            endpoint='createListOfGames', sindex='0'
        )},
        {'label': translation(30002), 'path': plugin.url_for(
            endpoint='createFollowingList'
        )},
        {'label': translation(30006), 'path': plugin.url_for(
            endpoint='createListOfTeams', sindex='0'
        )},
        {'label': translation(30003), 'path': plugin.url_for(
            endpoint='search'
        )},
        {'label': translation(30004), 'path': plugin.url_for(
            endpoint='showSettings'
        )}
    ]
    return items


@plugin.route('/createFollowingList/')
def createFollowingList():
    items = []
    username = settings.getSetting('username').lower()
    if not username:
        settings.openSettings()
        username = settings.getSetting('username').lower()
    #Using xml in this case, because it's alot faster than parsing throw the big json result
    xmlDataOnlineStreams = downloadWebData(
        url='http://api.justin.tv/api/stream/list.xml')
    jsonData = getJsonFromTwitchApi(
        url='http://api.justin.tv/api/user/favorites/' + username + '.json')
    if jsonData is None:
        return
    for x in jsonData:
        name = x['status']
        image = x['image_url_huge']
        loginname = x['login']
        if len(name) <= 0:
            name = loginname
        if xmlDataOnlineStreams.count('<login>'+loginname+'</login>') > 0:
            items.append({'label': name, 'path': plugin.url_for(
                endpoint='playLive', name=loginname
            )})
    return items


@plugin.route('/createListOfFeaturedStreams/')
def createListOfFeaturedStreams():
    items = []
    jsonData = getJsonFromTwitchApi(
        url='https://api.twitch.tv/kraken/streams/featured')
    if jsonData is None:
        return
    for x in jsonData['featured']:
        try:
            image = x['stream']['channel']['logo']
            image = image.replace("http://", "", 1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        name = x['stream']['channel']['status']
        if name == '':
            name = x['stream']['channel']['display_name']
        channelname = x['stream']['channel']['name']
        items.append({'label': name, 'path': plugin.url_for(
                endpoint='playLive', name=channelname, thumbnail = x['stream']['channel']['logo']
            )}, 'is_playable': True)
    return items


@plugin.route('/createListOfTeams/')
def createListOfTeams():
    #Temporary solution until twitch api method is available
    items = []
    jsonString = downloadWebData(url='https://spreadsheets.google.com/feeds/list/0ArmMFLQnLIp8dFJ5bW9aOW03VHY5aUhsUFNXSUl1SXc/od6/public/basic?alt=json')
    if jsonString is None:
        return
    try:
        jsonData = json.loads(jsonString)
    except:
        xbmc.executebuiltin('XBMC.Notification("' + translation(
            32008) + '","' + translation(32008) + '")')
        return
    for x in jsonData['feed']['entry']:
        teamData = x['content']['$t'].split(',')
        try:
            image = teamData[1][7:]
            image = image.replace("http://", "", 1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        name = x['title']['$t']
        channelname = teamData[0][7:]
        items.append({'label': name, 'path': '...'})  # TODO fixme
    return items


@plugin.route('/createListOfTeamStreams/<team>/')
def createListOfTeamStreams(team):
    items = []
    jsonData = getJsonFromTwitchApi(url='http://api.twitch.tv/api/team/' + urllib.quote_plus(team) + '/live_channels.json')
    if jsonData is None:
        return
    for x in jsonData['channels']:
        try:
            image = x['channel']['image']['size600']
            image = image.replace("http://", "", 1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        if x['channel']['title'] is None:
            name = x['channel']['display_name']
        else:
            name = x['channel']['display_name'] + ' - ' + x['channel']['title']
        channelname = x['channel']['name']
        items.append({'label': channelname, 'path': '...'})  # TODO Fixme
    return items


@plugin.route('/createListOfGames/<sindex>/')
def createListOfGames(sindex):
    index = int(sindex)
    items = []
    jsonData = getJsonFromTwitchApi(url='https://api.twitch.tv/kraken/games/top?limit=' + str(ITEMS_PER_SITE) + '&offset=' + str(index * ITEMS_PER_SITE))
    if jsonData is None:
        return
    for x in jsonData['top']:
        try:
            name = str(x['game']['name'])
            game = urllib.quote(name)
            image = ''
        except:
            continue
        try:
            image = x['game']['images']['super']
            image = image.replace("http://", "", 1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ''
        items.append({'label': name, 'path': plugin.url_for(
            'createListForGame', gameName=name, sindex='0')})
    if len(jsonData['top']) >= ITEMS_PER_SITE:
        items.append({'label': translation(31001), 'path': plugin.url_for(
            'createListOfGames', sindex=str(index + 1))})
    return items


@plugin.route('/search/')
def search():
    items = []
    keyboard = xbmc.Keyboard('', translation(30101))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = urllib.quote_plus(keyboard.getText())
        sdata = downloadWebData('http://api.swiftype.com/api/v1/public/engines/search.json?callback=jQuery1337&q=' + search_string + '&engine_key=9NXQEpmQPwBEz43TM592&page=1&per_page=' + str(ITEMS_PER_SITE))
        sdata = sdata.replace('jQuery1337', '')
        sdata = sdata[1:len(sdata) - 1]
        jdata = json.loads(sdata)
        records = jdata['records']['broadcasts']
        for x in records:
            items.append({'label': x['title'], 'path': plugin.url_for(
                endpoint='playLive', name=x['user']
            )})
        return items


@plugin.route('/createListForGame/<gameName>/<sindex>/')
def createListForGame(gameName, sindex):
    index = int(sindex)
    items = []
    print('https://api.twitch.tv/kraken/streams?game=' + urllib.quote_plus(gameName) + '&limit=' + str(ITEMS_PER_SITE) + '&offset=' + str(index * ITEMS_PER_SITE) + '\n\n')
    jsonString = downloadWebData(url='https://api.twitch.tv/kraken/streams?game=' + urllib.quote_plus(gameName) + '&limit=' + str(ITEMS_PER_SITE) + '&offset=' + str(index * ITEMS_PER_SITE))
    if jsonString is None:
        return
    jsonData = json.loads(jsonString)
    try:
        jsonData = json.loads(jsonString)
    except:
        xbmc.executebuiltin('XBMC.Notification("' + translation(
            32008) + '","' + translation(32008) + '")')
        return
    for x in jsonData['streams']:
        try:
            image = x['channel']['logo']
            image = image.replace("http://", "", 1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        name = x['channel']['status']
        if name == '':
            name = x['channel']['display_name']
        items.append({'label': name, 'path': '...'})  # TODO Fixme
    if len(jsonData['streams']) >= ITEMS_PER_SITE:
        items.append({'label': translation(31001), 'path': plugin.url_for(
            'createListForGame', gameName=gameName, sindex=str(index + 1))})
    return items


@plugin.route('/showSettings/')
def showSettings():
    #there is probably a shorter way to do this
    settings.openSettings()


def get_request(url, headers=None):
    try:
        if headers is None:
            headers = {'User-agent': httpHeaderUserAgent,
                       'Referer': 'http://www.twitch.tv/'}
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
        return link
    except urllib2.URLError, e:
        errorStr = str(e.read())
        if hasattr(e, 'code'):
            if str(e.code) == '403':
                if 'archive' in url:
                    xbmc.executebuiltin("XBMC.Notification(" + translation(
                        31000) + "," + translation(32003) + " " + name + ")")
            xbmc.executebuiltin("XBMC.Notification(" + translation(
                31000) + "," + translation(32001) + ")")


def getSwfUrl(channel_name):
    # Helper method to grab the swf url, resolving HTTP 301/302 along the way
    base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': 'http://www.justin.tv/' + channel_name}
    req = urllib2.Request(base_url, None, headers)
    response = urllib2.urlopen(req)
    return response.geturl()


def getBestJtvTokenPossible(name):
    # Helper method to find another jtv token
    swf_url = getSwfUrl(name)
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': swf_url}
    url = 'http://usher.justin.tv/find/' + name + '.json?type=any&group='
    data = json.loads(get_request(url, headers))
    bestVideoHeight = -1
    bestIndex = 0
    index = 0
    for x in data:
        value = x.get('token', '')
        videoHeight = int(x['video_height'])
        if (value != '') and (videoHeight > bestVideoHeight):
            bestVideoHeight = x['video_height']
            bestIndex = index
        index = index + 1
    return data[bestIndex]


@plugin.route('/playLive/<name>/')
def playLive(name):
    swf_url = getSwfUrl(name)
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': swf_url}
    chosenQuality = settings.getSetting('video')
    videoTypeName = 'any'
    if chosenQuality == '0':
        videoTypeName = 'any'
    elif chosenQuality == '1':
        videoTypeName = '720p'
    elif chosenQuality == '2':
        videoTypeName = '480p'
    elif chosenQuality == '3':
        videoTypeName = '360p'
    url = 'http://usher.justin.tv/find/' + name + '.json?type=' + \
        videoTypeName + '&private_code=null&group='
    data = json.loads(get_request(url, headers))
    tokenIndex = 0

    try:
        # trying to get a token in desired quality
        token = ' jtv=' + data[tokenIndex]['token'].replace(
            '\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        rtmp = data[tokenIndex]['connect'] + '/' + data[tokenIndex]['play']
    except:
        xbmc.executebuiltin("XBMC.Notification(" + translation(
            32005) + "," + translation(32006) + ")")
        jtvtoken = getBestJtvTokenPossible(name)
        if jtvtoken == '':
            xbmc.executebuiltin("XBMC.Notification(" + translation(
                31000) + "," + translation(32004) + ")")
            return
        token = ' jtv=' + jtvtoken['token'].replace(
            '\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        rtmp = jtvtoken['connect'] + '/' + jtvtoken['play']

    swf = ' swfUrl=%s swfVfy=1 live=1' % swf_url
    Pageurl = ' Pageurl=http://www.justin.tv/' + name
    url = rtmp + token + swf + Pageurl
    item = {
        'label': name,
        'path': url,
    }
    return plugin.play_video(item)


if __name__ == '__main__':
    plugin.run()
