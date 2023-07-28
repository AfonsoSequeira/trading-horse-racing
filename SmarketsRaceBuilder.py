import sys
from smarketsClient import client as sm_client
import datetime
import requests
import numpy as np
import math
import re
from itertools import groupby

def get_bids_and_offers(x):
    try:
        return (round((10000/x["offers"][0]["price"]),2) , round((10000/x["bids"][0]["price"]),2))
    except:
        return None
    
class SmarketsHorseRacingMarket:
    
    def __init__(self, name = None, tag = None, event_name =  None):
        self.name = name
        self.tag = tag
        self.event_name = event_name
        self.prices = [None, None, None, None, None, None, None]
        
    def setPrice(self, place_number, price):
        self.prices[place_number - 1] = price
        
    def getInfo(self):
        print("|Tag: ", self.tag,
              "\n|Event name: ",self.event_name,
              "\n|Name: ", self.name,
              "\n|Prices: ", self.prices)
        
        
def createSmarketsEventsAndRaces(client, start_date_min, start_date_max):
    events = client.get_available_events(['upcoming'],
                                         ['horse_racing_race'],
                                         ['horse_racing'],
                                         start_date_max ,
                                         20 ,
                                         start_date_min)
    markets = client.get_related_markets(events)
    
    return events, markets
        
        

def createSmarketsMappings(client, events, markets):
    event_list = []
    parent_event_ids = []
    for event in events:
        event_list.append((event["parent_id"],event["id"], event["name"], event["start_date"]))
        parent_event_ids.append(event["parent_id"])
        
    #get parent event dict
    parent_event_ids = np.unique(np.array(parent_event_ids))
    parent_events = client.get_events(parent_event_ids)
    parent_event_dict = {}
    parent_event_names = []
    for event in parent_events:
        eventName = re.sub("[\(\[].*?[\)\]]", "", event["name"])
        strList = eventName.split(" ")
        name = strList[-1] + "!".join(strList[0:-1])
        name = name.lower().replace(" ", "-")#[0:min(8, len(event["name"]))]
        parent_event_dict[event["id"]] = name
        parent_event_names.append(name)
        
    #get event dict
    new_event_list = [(k + "-" + parent_event_dict[x] + "/" + z, y) for (x,y,z,k) in event_list ]
    oddsCheckerUrlList = ["https://www.oddschecker.com/horse-racing/" + tag + "/winner" for (tag,_) in new_event_list]
    event_dict = {}
    for event in new_event_list:
        event_dict[event[1]] = event[0]
        
    #get market dict
    market_dict = {}
    for market in markets:
        if market["market_type"]["name"] == "WINNER":
            market_dict[market["id"]] = { 'event_id' : market["event_id"] , 'type' :  1}
        else:
            market_dict[market["id"]] = { 'event_id' : market["event_id"] , 'type' :  market["market_type"]["param"]}
            
    return event_dict, market_dict, oddsCheckerUrlList


def extractSmarketsPrices(client, markets, market_dict, event_dict):
    contracts = client.get_related_contracts(markets)
    market_id_list = [x["id"] for x in markets]
    quotes = client.get_quotes(market_id_list)
    
    bid_dict = {}
    quote_keys = list(quotes.keys())
    quote_vals = list(quotes.values())
    for i in range(0, len(quotes)):
        bid_dict[quote_keys[i]] = get_bids_and_offers(quote_vals[i])
        
    
    price_list = []
    for idx in range(len(contracts)):
        market_id = contracts[idx]["market_id"]
        event_name = event_dict[market_dict[market_id]["event_id"]]
        market_type = market_dict[market_id]["type"]
        name = contracts[idx]["name"].replace(" ", "-").lower()
        comb_name = event_name + "_" + name
        bid = bid_dict[contracts[idx]["id"]]
        
        price_list.append({ 'comb_name' : comb_name , 'event_name' : event_name , 'name' : name, 'market_type' : market_type, 'bid' : bid})
    
    return price_list 


def createSmarketsFinalPrices(price_list):
    def key_name(k):
        return k['comb_name']
    
    price_list = sorted(price_list, key = key_name)
    
    smarkets_racing_list = []
    for key, value in groupby(price_list, key_name):
        instances = list(value)
        name = instances[0]["name"]
        tag = instances[0]["comb_name"]
        event_name = instances[0]["event_name"]
        new_race = SmarketsHorseRacingMarket(name , tag , event_name)
        for i in instances:
            new_race.setPrice(int(i["market_type"]), i["bid"])
        smarkets_racing_list.append(new_race)
        
    return smarkets_racing_list


def smarketsRaceBuilder(hoursTreshold):
    client = sm_client.SmarketsClient()
    client.init_session()
    
    start_date_min = datetime.datetime.now()+ datetime.timedelta(minutes = 3)
    start_date_max = datetime.datetime.now()+ datetime.timedelta(hours = hoursTreshold)
    
    events, markets = createSmarketsEventsAndRaces(client, start_date_min, start_date_max)
    event_dict, market_dict, urlList = createSmarketsMappings(client, events, markets)
    
    price_list = extractSmarketsPrices(client, markets, market_dict, event_dict)
    smarketsObjects = createSmarketsFinalPrices(price_list)
    
    return smarketsObjects, urlList

#smarketsPrices, urlList = smarketsRaceBuilder(24) 

# for url in urlList:
#     print(url)

    

