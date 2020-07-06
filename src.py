"""
The following code allows us to crawl basketball-reference.com 
and scrape data pertaining to team and/or individual player data, 
for a specified year range.
"""

#%%
import pandas as pd 
import random
import numpy as np
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString, Tag
import datetime
from urllib.parse import urlparse
from pprint import pprint as pp


#%%
nbaDict = dict( 
    # this dict is used so we can input 'Hawks' instead of 'ATL', for instance
    # the goal is to not have to rememver abbreviations
    Hawks = 'ATL',
    Celtics = 'BOS',
    Nets = 'NJN',
    Hornets = 'CHA',
    Bulls = 'CHI',
    Cavaliers = 'CLE',
    Mavericks = 'DAL',
    Nuggets = 'DEN',
    Pistons = 'DET',
    Warrios = 'GSW',
    Rockets = 'HOU',
    Pacers = 'IND',
    Clipprs = 'LAC',
    Lakers = 'LAL',
    Memphis = 'MEM',
    Heat = 'MIA',
    Bucks = 'MIL',
    Timberwolves = 'MIN',
    Pelicans = 'NOH',
    Knicks = 'NYK',
    Thunder = 'OKC',
    Magic = 'ORL',
    Suns = 'PHO',
    Trailblazers = 'POR',
    Kings = 'SAC',
    Spurs = 'SAS',
    Raptors = 'TOR',
    Jazz = 'UTA',
    Wizards = 'WAS',
)
nbaDict['76ers'] = 'PHI' # had to enter separately because of syntax used to define teamDict above

#%%
# Beginning of code pertaining to team data
#%%
def findYearPage(team, year):
    """
    Finds URL for given team and year on basketball-reference.com

    Parameters:
    team: str
        team name input. should only include team name, not city. eg 'Lakers', 'Nuggets', etc.
    year: int or str
        year for which you want data. if 2009 is input, then season ENDING in 2009 is relevant year
    
    Returns:
    address: str
        string representing URL for given team and year
    """

    team = nbaDict[team]
    year = str(year)
    address = f'https://www.basketball-reference.com/teams/{team}/{str(year)}_games.html'
    return address

if __name__ == '__main__':
    address = findYearPage('Lakers', '1961')
    print(address)

#%%
def findNextSeason(bs_object):
    '''
    Finds next season URL 
    So if we're currently on 2005-2006 page for Pistons, this def will find URL for 2006-2007 page

    Parameters
    bs_object: BeautifulSoup object
        bs object obtained by way of code similar to:
            html = urlopen(url)
            bs = BeautifulSoup(html.read(), 'html5lib')
            nextSeason = findNextSeason(bs)
    
    Returns
    nextHTML: str
        string representing URL of next relevant season
    '''
    bs = bs_object
    ourTag = bs.find('div', {'class':'prevnext'})
    if ourTag.find('div', {'class':'button2 next'}):
        for child in ourTag.children:
            if isinstance(child, NavigableString):
                continue
            if isinstance(child, Tag):
                if child.find('div', {'class':'button2 next'}):
                    nextHTML = child.attrs['href']
                    nextHTML = 'https://www.basketball-reference.com' + nextHTML
        return nextHTML
    else:
        return False
        # finish writing this to see if I need to change this

if __name__ == '__main__':
    html = urlopen('https://www.basketball-reference.com/teams/LAL/1961_games.html')
    bs = BeautifulSoup(html.read(), 'html5lib')
    nextHTML = findNextSeason(bs)
    print(type(nextHTML), nextHTML)


#%%
def getTeamDict(team, beginYear, endYear):
    """
    Compiles a dictionary of pandas dataframes, with keys being years, and values being corresponding team statistics
    
    An option to just scrape all seasons would have been included in this def, with 
    beginYear and endYear being optional arguments. However, due to the way basketball-reference.com is 
    structured, you have to specify a page to begin at. There isn't an option to just begin at a team's
    very first season page.

    Parameters
    team: str
        str corresponding to team for which you want to compile dataframes
        Team codes: see teamDict
    beginYear: int or str
        year from which you want to start gathering data. 1961 means seasin ENDING in 1961
    endYear: int or str
        endYear is noninclusive of data that will be included. So if endYear = 2005, data will 
        pertain to season ending in 2004
    
    Returns
    teamDict: dict
        dict of key:value pairs of year:(pandas dataframe of team stats for year)
    """
    
    teamDict = {}
    url = findYearPage(team, beginYear)
    endYearURL = findYearPage(team, endYear)
    df = pd.read_html(url, index_col = 'G')[0] # pd.read_html collects all relevant html tables into dataframes; we're interested in the first one
    teamDict[str(beginYear)] = df # we are creating a dictionary of pandas dataframes, with years as keys
    html = urlopen(url)
    bs = BeautifulSoup(html.read(), 'html5lib')
    nextSeason = findNextSeason(bs)
    year = str(int(beginYear) + 1)

    while nextSeason != endYearURL: # collect years until we hit our end year of interest
        df = pd.read_html(nextSeason, index_col = 'G')[0]
        teamDict[str(year)] = df
        html = urlopen(nextSeason)
        bs = BeautifulSoup(html, 'html5lib')
        nextSeason = findNextSeason(bs)
        year = str(int(year) + 1)
    
    return teamDict
    # Just have to initialize this first dataframe, then we can start crawling through pages

if __name__ == '__main__':
    ourDict = getTeamDict('Lakers', 1998, 2005)
    print(ourDict.keys())
    

#%%
# End of code pertaining to team data, beginning of code pertaining to individual player data
#%%
def findPlayerPage(lastName, firstName):
    '''
    Finds players profile page, if it exists

    Parameters
    tags: BeautifulSoup object
        BeautifulSoup object containing all html tags for index page for player's last name
    
    Returns
    playerPage: str
        str containing url of player's basketball reference page
    '''
    player = firstName + ' ' + lastName
    letter = lastName[0].lower() # letters are stored in lower case in URL for basketball reference
    html = urlopen(f'https://www.basketball-reference.com/players/{letter}/')
    bs = BeautifulSoup(html.read(), 'html5lib')
    tags = bs.find_all()
    for tag in tags:
        if tag.get_text() == player or tag.get_text() == player + '*':
        # some players have asterisks next to their names
            playerPage = 'https://www.basketball-reference.com' + tag.find('a').attrs['href']
            return playerPage

if __name__ == '__main__':
    newURL = findPlayerPage('Boykins', 'Earl')
    print(newURL)

#%%
def getSeasonList(playerPage):
    '''
    Creates a list of html tags pertaining to seasons in player's career

    Parameters
    playerPage: string
        string representing URL of player's profile page, such as:
            https://www.basketball-reference.com/players/b/boykiea01.html'
    
    Returns
    seasonList: list
        list of html link tags of form <a href=...>
    '''
    html = urlopen(playerPage)
    bs = BeautifulSoup(html.read(), 'html5lib')
    identifier = bs.find(text = 'Game Logs')
    div = identifier.parent.parent.parent
    seasonHeader = div.findNext('ul') # when dealing with tag, not bs object, we use findNext, instead of find 
    seasonList = list(seasonHeader.findAll('a'))
    if 'playoffs' in seasonList[-1].attrs['href']: # this gets rid of playoff link
        seasonList.pop()

    return seasonList
    
        
if __name__ == '__main__':
    playerPage = findPlayerPage('Johnson', 'Magic')
    seasonList = getSeasonList(playerPage)
    print(seasonList)

#%%
def extractYearList(seasonList):
    """
    Creates a list of years. Should be used by zipping together list of dataframes to 
    create year:dataframe dictionaries

    This def may seem a little clunky, but we need to be able to extract years from our html tags,
    so that we can use them to create a dictionary later with year:pd.dataframe as key:value pairs

    Parameters
    seasonList: list
        list of html tags of form <a href=...>

    returns 
    yearList: list
        list of years, in int form
    """

    yearList = []
    for season in seasonList:
        year = season.get_text().split('-')
        year = year[0]
        year = int(year) + 1
        yearList.append(year)
    return yearList

if __name__== '__main__':
    playerPage = findPlayerPage('Jordan', 'Michael')
    seasonList = getSeasonList(playerPage)
    years = extractYearList(seasonList)
    print(years)


#%%
def getCareerDict(lastName, firstName, beginYear, endYear):
    '''
    Creates a list of pandas dataframes, with each dataframe containing different career season

    Parameters
    SeasonList: list
        list of html link tags of form <a href=...>
    
    Returns
    playerCareerDict: dict
        dict with key:value pairs in form of year:playerYearStats
    '''
    playerPage = findPlayerPage(lastName, firstName)
    ourSeason = getSeasonList(playerPage) # this isn't being recognized for some reason
    yearList = extractYearList(ourSeason) # we'll use this in a zip to create keys for dictionary below
    yearList = yearList[yearList.index(beginYear):yearList.index(endYear)] # we do not want end year to be inclusive
    addresses = ['https://www.basketball-reference.com' + season.attrs['href'] for season in ourSeason]
    beginIndex = 0
    endIndex = 0

    amendedPlayerURL = playerPage[:-5] # this drops '.html' from end of playerPage
    for i, address in enumerate(addresses): # finding relevant begin and end year addresses
        if address == amendedPlayerURL + '/gamelog/' + str(beginYear):
            beginIndex = i
        if address == amendedPlayerURL + '/gamelog/' + str(endYear):
            endIndex = i
            break

    subAddresses = addresses[beginIndex:endIndex + 1]

    playerStatDataFrames = [pd.read_html(address)[-1] for address in subAddresses] # list of dataframes containing player stats for each year
    
    # actual season dataframe is the final entry, as there are multiple tables on 
    # each season page
    for playerSeason in playerStatDataFrames:
        #print(dataFrame.loc[:10])
        if '+/-' in playerSeason: 
            playerSeason.drop(['+/-'], axis = 1, inplace = True)
            #print(dataFrame.loc[:10])
            # +/- only appearedin 2000, so for players who 
            # straddle that year, this causes problems in the DF
            # so we're just removing the column with +/-
    
    # now create a dataframe of year:dataframe key:value pairs 
    playerCareerDict = {}
    for (year, dataframe) in zip(yearList, playerStatDataFrames):
        playerCareerDict[str(year)] = dataframe

    return playerCareerDict


if __name__ == '__main__':
    careerDict = getCareerDict('James', 'LeBron', 2008, 2010)

#%%
"""
Team and individual player functionality are working,
so let's create a team dictionary and a player dictionary for certain years
"""

if __name__ == '__main__':
    kobeDict = getCareerDict('Bryant', 'Kobe', 2008, 2012)
    lakersDict = getTeamDict('Lakers', 2008, 2012)

    for key in kobeDict:
        print(key)

    for key in lakersDict:
        print(key)

    for (kob, lak) in zip(kobeDict.items(), lakersDict.items()):
        print('kobe')
        pp(kob[1][:10]) # printing first ten entries for each year
        print() 
        print('lakers')
        pp(lak[1][:10])
        # I'm zipping here just for the sake of easily comparing and making sure games match up
        # since we input the same years, the games should match up
        # in other words, each dictionary should contain the same games, but one pertaining to team, 
        # and the other pertaining to player

