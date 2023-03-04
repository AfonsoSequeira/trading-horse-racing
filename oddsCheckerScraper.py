from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import json
from selenium.webdriver.chrome.options import Options
from bs4 import UnicodeDammit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import lxml.html as lh
from joblib import Parallel, delayed
import time

class OddsCheckerPrice:
    
    def __init__(self,bookmaker = None, name = None, price = None, ewDenom = None, ewPlaces =  None):
        self.name = name
        self.bookie = bookmaker
        self.price = price
        self.ewDenominator = ewDenom
        self.ewPlaces = ewPlaces
        
    def printPrice(self):
        print("Name: ", self.name,
              " Bookmaker: ", self.bookie,
              " Price: ", self.price,
              " ewDenom: ", self.ewDenominator,
              " ewPlaces: ", self.ewPlaces)
        
        
def oddsPortalScraper(prettyHTML, bookMakerList, url, log):
    
    finalPrices = []
    
    def split(list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i:i + chunk_size]
    
    soup = BeautifulSoup(prettyHTML, features="lxml")
    body = soup.body
    pricesHtml = body.find_all("td", class_= lambda value: value and 
                     (value.startswith("bc bs") or value.startswith("np o") or value.startswith("o np")))
    
    if log == True:
        f = open(url + ".txt", "wb")
        f.write(str(body).encode("utf-8"))
        f.close()
    
    pricesHtml = list(split(pricesHtml, len(bookMakerList)))
    
    namesHtml = body.find_all("a", class_ = "popup selTxt")
    
    horseNames = [x["data-name"].lower().replace(" ", "-") for x in namesHtml]
    
    for i in range(0, len(pricesHtml)):
        horsePricesHtml = pricesHtml[i]
        
        for b in range(0, len(bookMakerList)):
            priceHtml = horsePricesHtml[b]
            
            if priceHtml["data-o"] == "" or priceHtml.has_attr("data-ew-denom") == False:
                continue
            else:
                if "/" in priceHtml["data-o"]:
                    [numerator, denominator] = priceHtml["data-o"].split('/')
                    price = round((float(numerator) + float(denominator)) / float(denominator),2)
                
                elif priceHtml["data-o"] == 'SP':
                    price = "SP"
                else:
                    numerator = float(priceHtml["data-o"])
                    denominator = 1
                    price = round((float(numerator) + float(denominator)) / float(denominator),2)
                
                ewDenom = int(priceHtml["data-ew-denom"])
                ewPlaces = int(priceHtml["data-ew-places"])
                bookMakerName = bookMakerList[b]
                
                finalPrices.append(OddsCheckerPrice(bookMakerName,horseNames[i], price, ewDenom, ewPlaces))
                
    return finalPrices

def scrapeOddsCheckerRace(url, log = False):
    
    bookmakers = ["Bet365", "SkyBet", "PaddyPower", "WilliamHill", "888Sport",
             "Betfair", "BetVictor", "Coral", "UniBet", "SpreadEx", "BetFred",
             "BoyleSports", "10Bet", "BetUk", "SportingIndex", "LiveScoreBet",
             "QuinnBet", "BetWay", "LadBrokes", "PariMatch", "VBet",
             "SBK", "Tote", "BetFairExchange", "Smarkets", "MatchBook"]

    try:
        options = Options()
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36'
        options.add_argument('user-agent={0}'.format(user_agent))

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                            options=options)
        driver.get(url)
        
        if driver.current_url == "https://www.oddschecker.com/horse-racing":
            return []
        else:
            html_source_code = driver.execute_script("return document.body.innerHTML;")
            html_soup: BeautifulSoup = BeautifulSoup(html_source_code, 'html.parser')
            prettyHTML = html_soup.prettify()
            driver.close()
            
            prices = oddsPortalScraper(prettyHTML, bookmakers,url, log)
            
            return prices
    except:
        return []

def scrapeOddsChecker(urlList, log = False, isParallel = False):
    t0 = time.time()
    if isParallel == False:
        prices = []
        for i in range(0,len(urlList)):
            print("Scraping ", i + 1, " of ", len(urlList), " urls.")
            #need to add some validation to check whether this url exists, currenty not able to do so..
            try:
                racePrices = scrapeOddsCheckerRace(urlList[i], log)
                prices = prices + racePrices
                
            except:
                print(f"Error reading url: {urlList[i]}")
                continue
            
    else:
        prices = Parallel(n_jobs=-1, verbose= 5)(delayed(scrapeOddsCheckerRace)(url) for url in urlList)
        prices = sum(prices, [])

    t1 = time.time()
    print(f"Scraped oddsPortal urls in {t1-t0} ms.")
    return prices


# urlList = ["https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/16:00/winner",
#            "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/13:25/winner",
#             "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/15:30/winner",
#             "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/14:30/winner",
#             "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/16:30/winner",
#             "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/13:55/winner",
#             "https://www.oddschecker.com/horse-racing/2023-02-08-Ludlow/15:00/winner"]

# prices = scrapeOddsChecker(urlList, bookmakers, False, True)
# print(prices) 

# from math import sqrt
# t = Parallel(n_jobs=1)(delayed(sqrt)(i**2) for i in [1,2,3,"sd",5,6])
# print(t)