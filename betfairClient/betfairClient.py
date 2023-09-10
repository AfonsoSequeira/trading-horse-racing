import json
import pandas as pd
import requests, json, urllib
import datetime
# from  certifications.certification_paths import PATHS

CERTIFICATIONS_PATH = "C:/MyDevelopment/betfaircertifications/"

# "client2048":"C:/Users/User/Desktop/Betting/certifications/client-2048.pem",
# "configuration":"C:/Users/User/Desktop/Betting/certifications/configuration.toml"

def buildURL(startTime, now, event_name):
    if (startTime.date() - now.date()) == datetime.timedelta(days=1):

        formatted_date = startTime.strftime("%Y-%m-%d")
        formatted_time = startTime.strftime("%H:%M")

        url = "https://www.oddschecker.com/horse-racing/" + formatted_date + "-" + event_name.replace(" ", "-") + "/" + str(formatted_time) + "/winner"
    else:

        formatted_time = startTime.strftime("%H:%M")
        url = "https://www.oddschecker.com/horse-racing/" + event_name.replace(" ", "-") + "/" + str(formatted_time) + "/winner"

    return url

class betFairHorse:
    def __init__(self, name = None, tag = None, event_name =  None, date = None):
        self.name = name
        self.tag = tag
        self.event_name = event_name
        self.date = date
        self.prices = [None, None, None, None, None, None, None]
        
    def addPrice(self, place_number, price):
        self.prices[place_number - 1] = price
        
    def printPrice(self):
        print("Name: ", self.name,
              " Event: ", self.event_name,
              " Date: ", self.date,
              " Prices: ", self.prices)

        
class betFairClient:
    
    def __init__(self):
        self.username = "[username]"
        self.password = "[pwd]"
        self.app_key = "[application_key]"
        self.bet_url = None
        self.headers = None#{"X-Application" : self.app_key, "Content-Type" : "application/x-www-form-urlencoded"}
        
    def login(self):
        with open(CERTIFICATIONS_PATH + "betfair_details.json") as fh:
            login_details = json.load(fh)

        self.username = login_details["username"]
        self.password = login_details["pwd"]
        self.app_key = login_details["application_key"]

        payload = "username=" + self.username + "&password=" + self.password
        headers = {"X-Application" : self.app_key, "Content-Type" : "application/x-www-form-urlencoded"}

        resp = requests.post("https://identitysso-cert.betfair.com/api/certlogin",
                     data = payload,
                     cert = (CERTIFICATIONS_PATH + "betfairDB.crt", CERTIFICATIONS_PATH + "client-2048.pem"),
                     headers = headers)
        
        resp_json = resp.json()
        SSOID = resp_json["sessionToken"]
        
        self.bet_url = "https://api.betfair.com/exchange/betting/json-rpc/v1/"
        self.headers = {"X-Application": self.app_key, "X-Authentication": SSOID , "content-type": "application/json"}
        
    def getHorseRacingEvents(self):
        today = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        tomorrow = (datetime.datetime.now() + datetime.timedelta(hours = 24)).strftime('%Y-%m-%dT%H:%M:%SZ')

        event_filter = {
            'filter' : {
                "eventTypeIds":[7],
                "marketCountries":["GB", "IE"],
                "marketStartTime":{"from": today ,"to": tomorrow}
            }
        }

        events_req = requests.post(
            self.bet_url,
            headers= self.headers,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'SportsAPING/v1.0/listEvents',
                'params': event_filter,
                'id': 1
            })
            )

        jsonResponse = events_req.json()
        
        events = []
        for x in jsonResponse["result"]:
            try:
                if "RFC" in x["event"]["name"] or "F/C" in x["event"]["name"]:
                    continue
                else:
                    events.append((x["event"]["venue"], x["event"]["id"]))
            except:
                continue
            
        return events

    def getEventUrls(self, event_id, event_name, t_thresh, is_bst):

        time_min = (datetime.datetime.now() + datetime.timedelta(minutes = 10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        time_max = (datetime.datetime.now() + datetime.timedelta(hours = t_thresh)).strftime('%Y-%m-%dT%H:%M:%SZ')

        event_filter = {
            'filter': {
                'eventIds': [event_id],
                'marketTypeCodes': ['WIN'],
                'marketCountries': ["GB","IE"],
                'marketStartTime': {
                    'from': time_min,
                    'to': time_max
                }
            },
            'maxResults': 100,
            'marketProjection': ['MARKET_START_TIME']
        }

        markets_req = requests.post(
            self.bet_url,
            headers= self.headers,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'SportsAPING/v1.0/listMarketCatalogue',
                'params': event_filter,
                'id': 1
            })
            )

        markets = markets_req.json()['result']
        race_times = list(set([market['marketStartTime'] for market in markets]))
        race_times = [datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ") for x in race_times]
        if is_bst == True:
            race_times = [r + datetime.timedelta(hours = 1) for r in race_times]

        now = datetime.datetime.now()
        urls = [buildURL(x, now, event_name) for x in race_times]

        return urls

    def getAllBetfairUrls(self,t_thresh, is_bst):

        events = self.getHorseRacingEvents()
        url_list = [self.getEventUrls(event_id, event_name, t_thresh, is_bst) for event_name, event_id in events]
        url_list = sum(url_list, [])

        return url_list

    def getEventMarketTypes(self, event_id, event_name):
        event_filter = {
            'filter': {
                'eventIds': [event_id],
                'marketTypeCodes': ['WIN'],
                'marketCountries': ["GB","IE"],
            },
            'maxResults': 100,
            'marketProjection': ['MARKET_START_TIME']
        }

        markets_req = requests.post(
            self.bet_url,
            headers= self.headers,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'SportsAPING/v1.0/listMarketTypes',
                'params': event_filter,
                'id': 1
            })
            )

        markets = markets_req.json()['result']
        print(markets)
        

    def getEventMarkets(self, event_id, t_thresh):
        time_min = (datetime.datetime.now() + datetime.timedelta(minutes = 10))
        time_min_s = time_min.strftime('%Y-%m-%dT%H:%M:%SZ')

        time_max = (datetime.datetime.now() + datetime.timedelta(hours = t_thresh))
        time_max_s = time_max.strftime('%Y-%m-%dT%H:%M:%SZ')

        filter = {
            'filter': {
                'eventIds': [event_id],
                'marketTypeCodes': ['WIN', 'OTHER_PLACE'],
                'marketBettingType':'ODDS',
                'marketCountries': ["GB","IE"],
                "numberOfWinners": 1,
                'marketStartTime': {
                    'from': time_min_s,
                    'to': time_max_s
                }
            },
            'maxResults': 100,
            'marketProjection': ["EVENT","RUNNER_DESCRIPTION","MARKET_START_TIME", "MARKET_DESCRIPTION"]
        }

        markets_req = requests.post(
            self.bet_url,
            headers= self.headers,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'SportsAPING/v1.0/listMarketCatalogue',
                'params': filter,
                'id': 1
            })
            )

        #listMarketsRequest = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", "params": {"filter":{"eventIds":["' + event_id + '"],"marketCountries":["GB","IE"]}, "maxResults":"100", "marketTypeCodes":["WIN","OTHER_PLACE"], "marketStartTime":{"from":"' + time_min_s + '"}, "marketStartTime":{"to":"' + time_max_s + '"}, "marketBettingType":"ODDS", "numberOfWinners": "1", "marketProjection":["EVENT","RUNNER_DESCRIPTION","MARKET_START_TIME", "MARKET_DESCRIPTION"]}, "id": 1}'
        #req = requests.post(self.bet_url, listMarketsRequest.encode("utf-8"), headers = self.headers)

        jsonResponse = markets_req.json()
        
        compList = []
        times = []
        for market in jsonResponse["result"]:
            market_id = market["marketId"]
            startTime = market["marketStartTime"]
            market_type = market["description"]["marketType"]
            
            # Convert the string to a datetime object
            startTime = datetime.datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Format the hour and minute parts of the datetime object
            startDate = startTime.strftime("%H:%M")
            
            if market_type == "EACH_WAY" or market_type == 'MATCH_BET' or startTime > time_max or startTime < time_min:
                continue
            else:
                horses = [x["runnerName"] for x in market["runners"]]
                compList.append((market_id, startDate, horses))
                times.append(startTime)
        
        event_times = list(set(times))
        return compList,event_times
    
    def getMarketPrices(self, market_id):

        markets_req = requests.post(
            self.bet_url,
            headers= self.headers,
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'SportsAPING/v1.0/listMarketBook',
                'params': {
                    'marketIds': [market_id],
                    'priceProjection': {'priceData':['EX_BEST_OFFERS'], 'virtualise':'true'}
                },
                'id': 1
            })
            )

        # listPricesRequest = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds":["' + market_id + '"],"priceProjection":{"priceData":["EX_BEST_OFFERS"],"virtualise":"true"}}, "id": 1}'
        # req = requests.post(self.bet_url, listPricesRequest.encode("utf-8"), headers = self.headers)

        runnerPrices = markets_req.json()    
        marketPlaceNumber = runnerPrices["result"][0]["numberOfWinners"]
        
        horsePriceList = []
        for horseIdx in range(0, len(runnerPrices["result"][0]["runners"])):
            if runnerPrices["result"][0]["runners"][horseIdx]["status"] == 'ACTIVE':
                backPrices = runnerPrices["result"][0]["runners"][horseIdx]["ex"]["availableToBack"]
                layPrices = runnerPrices["result"][0]["runners"][horseIdx]["ex"]["availableToLay"]
                if len(backPrices) == 0 or len(layPrices) == 0:
                    backLayPrices = None
                else:
                    horseBackPrice = backPrices[0]["price"]
                    horseLayPrice = layPrices[0]["price"]

                    backLayPrices = (horseBackPrice, horseLayPrice)
                      
            else:
                continue

            horsePriceList.append(backLayPrices)
        return marketPlaceNumber, horsePriceList
    
    def getHorsesForEvent(self, event_id, event_name, t_thresh):
        markets, times = self.getEventMarkets(event_id, t_thresh)
        print(f"Getting horses for event {event_name}")
        #now = datetime.datetime.now()
        #urls = [buildURL(x, now, event_name) for x in times]

        allRaces = []
        allRaces = pd.DataFrame(columns = ["EventName", "Date","Places" , "RunnerName", "Prices"])
        for market in markets:
            data = []
            market_id, date, runnerNames = market
            places, prices = self.getMarketPrices(market_id)
            
        
            for i in range(0, len(prices)):
                #data.append((event_name, date, places, runnerNames[i], prices[i]))
                allRaces.loc[len(allRaces)]= [event_name, date, places, runnerNames[i], prices[i]]

            #allRaces.append(data)
            
        perHorseData = [(name, prices) for (name, prices) in allRaces.groupby("RunnerName")]
        
        horsePriceList = []
        for horse in perHorseData:
            idx = 0
            for _, race in horse[1].iterrows():
                idx += 1
                if idx == 1:
                    new_horse = betFairHorse(horse[0].lower().replace(" ", "-"), "notag", event_name, race["Date"])
                    new_horse.addPrice(race["Places"], race["Prices"])
                else:
                    new_horse.addPrice(race["Places"], race["Prices"])
                    
            horsePriceList.append(new_horse)
            
        return horsePriceList
    
    def getAllHorsePrices(self,t_thresh):
        all_horses = []
        events = self.getHorseRacingEvents()
        
        for event_name, event_id in events:
            horses_in_event = self.getHorsesForEvent(event_id, event_name, t_thresh)
            all_horses.append(horses_in_event)

            
        return sum(all_horses,[])


if __name__ == '__main__':

    betCl = betFairClient()
    betCl.login()
    betFairPrices = betCl.getAllHorsePrices(24)
    urls = betCl.getAllBetfairUrls(24, is_bst=True)

    for x in urls:
        print(x)

