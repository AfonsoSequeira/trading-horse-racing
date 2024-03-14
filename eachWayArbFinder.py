import sys
sys.path.append("C:/Users/User/Desktop/Learning/Betting/kelly-criterion-staking")

from oddsCheckerScraper import scrape_odds_checker
#from SmarketsRaceBuilder import smarketsRaceBuilder
from kellyStaking import kelly
from betfairClient.betfairClient import betFairClient
import pandas as pd
import datetime
import time


class matchedPrice:
    def __init__(self, name = None, bookmaker = None, event_name =  None, event_date = None,
                 currentPrice = None, exchangeWinPrices = None, exchangePlacePrices = None,
                 places = None, value = None, oddsProbsInfo = None, comments = None):
        self.name = name
        self.bookie = bookmaker
        self.event_name = event_name
        self.event_date = event_date
        self.currentPrice = currentPrice
        self.exchangeWinPrices = exchangeWinPrices
        self.exchangePlacePrices = exchangePlacePrices
        self.oddsProbsInfo = oddsProbsInfo
        self.places = places
        self.value = value
        self.comments = comments
        self.kelly_stake = None
        
    def printInfo(self):
        print("---> Name: ", self.name,
              "\n|Bookmaker: ", self.bookie,
              "\n|Event name: ",self.event_name,
              "\n|Event date: ",self.event_date,
              "\n|Current bookie price: ", self.currentPrice,
              "\n|Current exchange win price: ", self.exchangeWinPrices,
              "\n|Current exchange place price: ", self.exchangePlacePrices,
              "\n|Value: ", self.value,
              "\n|Kelly stake: ", self.kelly_stake)

    def getKellyStake(self, fractionalKelly):
        if self.oddsProbsInfo == None or len(self.oddsProbsInfo) != 4:
            raise("Error: tried to get kelly stake for negative value race.")

        probWin = self.oddsProbsInfo[0]
        oddsWin = self.oddsProbsInfo[1]
        probPlace = self.oddsProbsInfo[2]
        oddsPlace = self.oddsProbsInfo[3]
        self.kelly_stake = fractionalKelly * getEachWayKellyStake(oddsWin, oddsPlace, probWin, probPlace)

def getEachWayKellyStake(oddsWin, oddsPlace, probWin, probPlace):
    oddsA = (oddsWin + oddsPlace)/2
    oddsB = oddsPlace/2
    probA = probWin
    probB = probPlace - probWin

    rec_kelly = kelly.threeOutcomeKellyStake(oddsA, probA, oddsB, probB)
    return rec_kelly

#race comparison, function to take a list of exchange horse racing markets and a list of bookie horse racing markets
def checkValue(exchange_market, winExchangeProbs, bookies_market, liquidity_settings):

    if bookies_market.price == "SP":
        return matchedPrice(exchange_market.name,
                                bookies_market.bookie,
                                exchange_market.event_name,
                                exchange_market.date, 
                                bookies_market.price,
                                exchange_market.prices[0], 
                                exchange_market.prices[bookies_market.ewPlaces - 1],
                                bookies_market.ewPlaces,
                                None,
                                None,
                                f"did not have to bookie price")
    else:
        placeOdds = exchange_market.prices[bookies_market.ewPlaces - 1]
        
        if placeOdds == None or placeOdds[1] == None:
            return matchedPrice(exchange_market.name,
                                bookies_market.bookie,
                                exchange_market.event_name,
                                exchange_market.date, 
                                bookies_market.price,
                                exchange_market.prices[0], 
                                exchange_market.prices[bookies_market.ewPlaces - 1],
                                bookies_market.ewPlaces,
                                None,
                                None,
                                f"did not have to place price")

        else:
            exchange_placeOddsBack, exchange_placeOddsLay = placeOdds
            exchange_place_probs_back, exchange_place_probs_lay = 1/exchange_placeOddsBack, 1/exchange_placeOddsLay
            
            perc_spread = abs(exchange_place_probs_back - exchange_place_probs_lay)/exchange_place_probs_back
            if perc_spread > liquidity_settings["placeMarketSpreadLimit"]:
                #return(None, f"exchange's place market above spread limit. Spread of {abs(exchange_place_probs_back - exchange_place_probs_lay)}", "NoValue")
                return matchedPrice(exchange_market.name,
                                bookies_market.bookie,
                                exchange_market.event_name,
                                exchange_market.date, 
                                bookies_market.price,
                                exchange_market.prices[0], 
                                exchange_market.prices[bookies_market.ewPlaces - 1],
                                bookies_market.ewPlaces,
                                None,
                                None,
                                f"exchange's place market above spread limit. Spread of {abs(exchange_place_probs_back - exchange_place_probs_lay)}")

            else:
                placeExchangeProbs = 0.5 * exchange_place_probs_back + 0.5 * exchange_place_probs_lay 
        
                placeOnlyProbs = placeExchangeProbs - winExchangeProbs
                bookieWin = bookies_market.price
                bookiePlace = ((bookieWin - 1)/bookies_market.ewDenominator) + 1

                winProfit = bookieWin + bookiePlace - 2
                placeProfit = bookiePlace - 2
                loseProfit = -2

                expectedProfit = winExchangeProbs * winProfit + placeOnlyProbs * placeProfit + (1 - placeExchangeProbs) * (loseProfit)
                expectedValue = (expectedProfit/2)
                
                if expectedValue > 0:
                    comment = "VALUE!"
                else:
                    comment = "No value."

                return matchedPrice(exchange_market.name,
                                bookies_market.bookie,
                                exchange_market.event_name,
                                exchange_market.date, 
                                bookies_market.price,
                                exchange_market.prices[0], 
                                exchange_market.prices[bookies_market.ewPlaces - 1],
                                bookies_market.ewPlaces,
                                expectedValue,
                                (winExchangeProbs, bookieWin, placeExchangeProbs, bookiePlace),
                                comment)

def comparePrices(exchange_market, bookies_prices, liquidity_settings):

    #conditions to filter out race exchange price from the start 
    ### - if win price does not exist or is does not have both bid and ask prices
    ### - if win price does not have enough liquidity
    ### - if bookies price is starting price, skip it
    if exchange_market.prices[0] == None or exchange_market.prices[0][1] == None:
        return [matchedPrice(exchange_market.name,
                                "All bookmakers",
                                exchange_market.event_name,
                                exchange_market.date, 
                                None,
                                exchange_market.prices[0], 
                                None,
                                None,
                                None,
                                None,
                                "did not have to-win price")]
    
    else:
        exchange_odds_back, exchange_odds_lay = exchange_market.prices[0]
        exchange_probs_back, exchange_probs_lay = 1/exchange_odds_back, 1/exchange_odds_lay

        perc_spread = abs(exchange_probs_back - exchange_probs_lay)/exchange_probs_back
        if perc_spread > liquidity_settings["winMarketSpreadLimit"]:
            return [matchedPrice(exchange_market.name,
                                "All bookmakers",
                                exchange_market.event_name,
                                exchange_market.date, 
                                None,
                                exchange_market.prices[0], 
                                None,
                                None,
                                None,
                                None,
                                f"exchange's to-win market above spread limit. Spread of {abs(exchange_probs_back - exchange_probs_lay)}")]

        else:
            winExchangeProbs = 0.5 * exchange_probs_back + 0.5 * exchange_probs_lay
            assessed_prices = [checkValue(exchange_market, winExchangeProbs, bookie_price, liquidity_settings) for bookie_price in bookies_prices]
                                
            return assessed_prices
        
def matchRaces(bookieRaces, exchangeRaces):
    paired_list = []
    for exchangePrice in exchangeRaces:
        bookiePrices = [x for x in bookieRaces if x.name.lower() == exchangePrice.name] 
        if not bookiePrices:
            continue 
        else:
            paired_list.append([exchangePrice, bookiePrices])
            
    return paired_list

def checkValueRaces(bookieRaces, exchangeRaces,liquidity_settings, frac_kelly_val):
    assessedMarketList = []
    valueFinds = []
    matchedRaces = matchRaces(bookieRaces, exchangeRaces)
    for exchange_price, bookies_prices in matchedRaces:
        assessedMarketList += comparePrices(exchange_price, bookies_prices, liquidity_settings)

    #iterate through assessed prices and find positive value
    for price in assessedMarketList:
        if price.value != None and price.value > 0:
            price.getKellyStake(frac_kelly_val)
            valueFinds.append(price)
             
    return valueFinds, assessedMarketList

def runValueFinder(h_thresh, is_bst,liquidity_settings,frac_kelly, logging, is_parallel, url_keyword=None):

    betCl = betFairClient()
    betCl.login()
    urls = betCl.getAllBetfairUrls(h_thresh, is_bst)

    if len(urls) == 0:
        print("no races within time frame")
        return betFairPrices, None
    else:
        if url_keyword != None: urls = [url for url in urls if url_keyword in url.lower()] 
        for url in urls: print(url)
        oddsCheckerPrices = scrape_odds_checker(urls, logging)
        betFairPrices = betCl.getAllHorsePrices(h_thresh, is_bst)
        valueFinds, allMarkets = checkValueRaces(oddsCheckerPrices, betFairPrices,liquidity_settings, frac_kelly)
        
        return betFairPrices, oddsCheckerPrices, valueFinds, allMarkets
    
def save_value_finds(value_finds:list, bookmakers_to_use) -> None:
    data = [vars(obj) for obj in value_finds]
    df = pd.DataFrame(data)
    df = df[df.bookie.isin(bookmakers_to_use)]

    date = datetime.datetime.now().date().__str__()
    hour = datetime.datetime.now().hour.__str__()
    minute = datetime.datetime.now().minute.__str__()

    str_date = f"{date}_{hour}_{minute}"
    df.to_csv("value_finds/" + str_date + "value_bets.csv", index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    
    liq_settings = {"winMarketSpreadLimit": 0.4 , "placeMarketSpreadLimit": 0.4}
    bookmakers_to_use = ["Bet365", "BetFred"]

    betfair_prices, odds_checker_prices, value_finds, all_markets = runValueFinder(25, False, liq_settings,
                                                                                   1.0, False, True,
                                                                                     url_keyword="chelt")
    save_value_finds(value_finds, bookmakers_to_use)

    stop = time.perf_counter()
    time_taken = stop - start
    print("Finished. Time taken:", time_taken)
    


