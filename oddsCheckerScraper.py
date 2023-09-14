from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import time
import asyncio

BOOKMAKERS = ["Bet365", "SkyBet", "PaddyPower", "WilliamHill", "888Sport",
             "Betfair", "BetVictor", "Coral", "UniBet", "SpreadEx", "BetFred", "BetMGM Uk",
             "BoyleSports", "10Bet", "StarSports", "BetUk", "SportingIndex", "LiveScoreBet",
             "QuinnBet", "BetWay", "LadBrokes", "BetGoodWin", "PariMatch", "VBet",
             "Tote", "BetFairExchange", "MatchBook"]

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

#version where the browser and context are always the same, gets blocked!
# async def fetch(browser, url):
#     async with semaphore:
#         page = await browser.new_page()
#         response = await page.goto(url)
#         if not response.ok:
#             raise Exception(f"Failed to load {url}")
#         print(f"Loaded page: {url}")
#         return await page.inner_html('div#outer-container')

# async def fetch_all(browser, urls):
#     tasks = []
#     for url in urls:
#         task = asyncio.create_task(fetch(browser, url))
#         tasks.append(task)
#     res = await asyncio.gather(*tasks)
#     return res

# async def main(urls):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(user_agent= 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36')
#         htmls = await fetch_all(context, urls)
#         await browser.close()

#     return htmls

semaphore = asyncio.Semaphore(20)

async def fetch(browser, url):
    async with semaphore:  # This will limit the number of concurrent tasks
        context = await browser.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36')
        page = await context.new_page()
        
        response = await page.goto(url)
        if not response.ok:
            await context.close()
            raise Exception(f"Failed to load {url}")

        print(f"Loaded page: {url}")
        html_content = await page.inner_html('div#outer-container')
        
        await context.close()  # Close the context after fetching to free up resources
        return html_content
    
async def fetch_all(browser, urls):
    tasks = [asyncio.create_task(fetch(browser, url)) for url in urls]
    return await asyncio.gather(*tasks)

async def main(urls):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        htmls = await fetch_all(browser, urls)
        await browser.close()

    return htmls

def scrape_odds(html_soup, bookMakerList, url, log):
    
    finalPrices = []
    
    def split(list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i:i + chunk_size]
    
    #soup = BeautifulSoup(prettyHTML, features="lxml")
    body = html_soup.body
    pricesHtml = body.find_all("td", class_= lambda value: value and 
                     (value.startswith("bc bs") or value.startswith("np o") or value.startswith("o np")))
    
    if log == True:
        f = open("text_logs.txt", "wb")
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
    
def scrape_odds_checker(url_list, log=False):
    start = time.perf_counter()
    inner_htmls  = asyncio.run(main(url_list))
    stop = time.perf_counter()
    time_taken = stop - start
    print("time taken:", time_taken)

    odds_checker_prices = []
    for html, url in list(zip(inner_htmls,url_list)):
        html_soup: BeautifulSoup = BeautifulSoup(html, 'lxml')
        prices = scrape_odds(html_soup, BOOKMAKERS,url, log)
        odds_checker_prices = odds_checker_prices + prices

    return odds_checker_prices


if __name__ == '__main__':
    urls =  [
        "https://www.oddschecker.com/horse-racing/2023-09-11-Brighton/16:40/winner",
        "https://www.oddschecker.com/horse-racing/2023-09-11-Brighton/17:45/winner",
        "https://www.oddschecker.com/horse-racing/2023-09-11-Brighton/17:15/winner",
        "https://www.oddschecker.com/horse-racing/2023-09-11-Brighton/14:55/winner",
        ]
    
    prices = scrape_odds_checker(urls,log=False)
    print("Finished")