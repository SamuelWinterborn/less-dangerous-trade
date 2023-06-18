import math

from . import api_edsm as api

"""
putting the api functions here first for possible overriding later
"""
def get_system_coord(systemName):
    return api.get_system_coord(systemName)

def is_system_anarchy(systemName):
    return api.is_system_anarchy(systemName)

def get_systems_in_radius(systemName, radius, minRadius=None, includeAnarchy=False):
    return api.get_systems_in_radius(systemName, radius, minRadius, includeAnarchy)

def get_stations(systemName, noPlanet=True):
    return api.get_stations(systemName, noPlanet)

def get_market_data(systemName, stationName):
    return api.get_market_data(systemName, stationName)

"""
Data Classes
"""
class MarketInfo:
    def __init__(self, marketD):
        self.marketD = marketD
        self.demandList = {}
        self.availableStock = {}

        # now parse the data for easier access later
        self.parse_data()

    # get list of demanded items
    def parse_data(self):
        # loop all market data
        for market in self.marketD:
            # add items with higher demand than stock to list
            if market["demand"] > market["stock"] - 5: #and market["demand"]:   # adding a bit of threshold
                self.demandList[market["id"]] = market

            # add items with available stock
            if market["stock"] > 0:
                self.availableStock[market["id"]] = market
        
        # sort demand list
        sorted(self.demandList.items(), key=lambda item: item[1]["demand"])

class StationInfo:
    def __init__(self, stationName, systemName):
        self.name = stationName
        self.systemName = systemName

        marketData = get_market_data(self.systemName, self.name)
        self.marketInfo = MarketInfo(marketData)

    """
    Extra functions
    """
    def __str__(self): 
        return "StationInfo({}/{})".format(self.systemName, self.name)
    
    def __repr__(self): 
        return self.__str__()

class SystemInfo:
    def __init__(self, systemName: str, coords: list=[0,0,0], distance: float=0):
        self.name = systemName
        self.coords = coords
        self.distance = distance

        self.stationToScan = []
        self.stationInfos = []

    def get_all_stationNames(self):
        self.stationToScan = get_stations(self.name)

    # run this to gather and keep stations and market infos
    def gather_station_infos(self):
        for stationName in self.stationToScan:
            self.stationInfos.append(StationInfo(stationName, self.name))

    def isolate_station(self, stationName):
        stationInfo = None
        for id, stationN in enumerate(self.stationToScan):
            if stationN == stationName:
                stationInfo = self.stationInfos[id]
                break

        if not stationInfo:
            print("ERROR: Failed to isolate station!")
            raise
        self.stationInfos = [stationInfo]
        self.stationToScan = [stationName]

    """
    Extra functions
    """
    def __str__(self): 
        return "SystemInfo({})".format(self.name)
    
    def __repr__(self): 
        return self.__str__()
    
    def copy(self):
        result = SystemInfo(self.name, self.coords, self.distance)
        result.stationToScan[:] = self.stationToScan[:]
        result.stationInfos[:] = self.stationInfos[:]
        return result
    
class RouteInfo:
    def __init__(self, fromSystem: SystemInfo, toSystem: SystemInfo, deviations: list, cargoSpace: int):
        self.cargoSpace = cargoSpace
        self.fromSystem = fromSystem
        self.toSystem = toSystem
        self.deviations = deviations

        print("LOG: Calculating trade between {} and {}".format(fromSystem, toSystem))
        straightRoutesDict = self.calcalate_between_2(fromSystem, toSystem)
        straightRouteName, straightRoute = self.pick_highest_profit_route(straightRoutesDict)
        self.routeName = straightRouteName
        self.route = straightRoute

        print("LOG: Straight route found, now calculate deviations...")
        deviateRoutesDict = self.calculate_with_deviation()
        if deviateRoutesDict:
            deviateRouteName, deviateRoute = self.pick_highest_profit_route(deviateRoutesDict)
            # if deviate route has a lot more profit, then assign as correct route
            if self.route:
                if deviateRoute["totalProfit"] > straightRoute["totalProfit"] * 3:
                    self.routeName = deviateRouteName
                    self.route = deviateRoute
            else:
                self.routeName = deviateRouteName
                self.route = deviateRoute


    def calculate_with_deviation(self):
        if not self.deviations:
            return None

        # first calculate the forwards first
        firstRouteDict = {}
        for deviate in self.deviations:
            curRouteDict = self.calcalate_between_2(self.fromSystem, deviate)
            if curRouteDict:
                firstRouteDict.update(curRouteDict)

        # then loop thru the forwards and calculate from there to destination system
        finalRouteDict = {}
        for firstRoute in firstRouteDict:
            # gather infos
            oldRouteDict = firstRouteDict[firstRoute]

            # calculate next route
            fromSystem = self.create_copy_of_last_system(firstRoute, oldRouteDict)
            curRouteDict = self.calcalate_between_2(fromSystem, self.toSystem)
            if not curRouteDict:
                continue

            # now combine and construct a new dict
            for newRoute in curRouteDict:
                newRouteName = firstRoute + " -> " + newRoute.split(" -> ")[-1]
                newItems = oldRouteDict["items"] + curRouteDict[newRoute]["items"]
                newProfit = oldRouteDict["totalProfit"] + curRouteDict[newRoute]["totalProfit"]
                newSystems = oldRouteDict["system_objs"]
                newSystems.append(self.toSystem)
                finalRouteDict[newRouteName] = self.construct_route(newRouteName, newItems, newProfit, newSystems)

        # done and return
        return finalRouteDict

    def calcalate_between_2(self, fromSystem: SystemInfo, toSystem: SystemInfo):
        toStations = toSystem.stationInfos
        fromStations = fromSystem.stationInfos

        routeDict = {}
        for toStat in toStations:
            for fromStat in fromStations:
                items, profit = self.get_profit_items(fromStat, toStat, self.cargoSpace, items=[], profit=0, excluded=[])
                if items and profit > 0:
                    routeName = "{}/{} -> {}/{}".format(fromSystem.name, fromStat.name, toSystem.name, toStat.name)
                    routeDict[routeName] = self.construct_route(routeName, [items], profit, [fromSystem, toSystem])
        return routeDict
    
    def get_profit_items(self, fromStat: StationInfo, toStat: StationInfo, cargoSpace: int, items: list=[], profit=0, excluded: list=[]):
        highestItem, highestItemName, highestProfit = self.get_highest_profit_item(fromStat, toStat, excluded)
        if highestItem:
            curAvailableStock = fromStat.marketInfo.availableStock[highestItem]["stock"]
            stockTaking = min(curAvailableStock, cargoSpace)
            curProfit = highestProfit * stockTaking
            items.append({
                "itemId" : highestItem,
                "itemName" : highestItemName,
                "count" : stockTaking,
                "profit" : curProfit
            })
            profit += curProfit
            cargoSpace -= curAvailableStock
            if cargoSpace > 0:
                excluded.append(highestItem)
                items, profit = self.get_profit_items(fromStat, toStat, cargoSpace, items, profit, excluded)
        return items, profit

    # item with highest profit in 2 stations
    def get_highest_profit_item(self, fromStat: StationInfo, toStat: StationInfo, excluded: list=[]):
        profit = 0
        item = ""
        itemName = ""
        demandList = toStat.marketInfo.demandList
        stockList = fromStat.marketInfo.availableStock
        for itemKey in demandList:
            if itemKey in stockList:
                curProfit = demandList[itemKey]["sellPrice"] - stockList[itemKey]["buyPrice"]
                if curProfit > profit and itemKey not in excluded:
                    profit = curProfit
                    item = itemKey
                    itemName = demandList[itemKey]["name"]
        return item, itemName, profit
                
    def pick_highest_profit_route(self, routeDict):
        bestRoute = None
        bestRouteName = None
        profit = 0
        for route in routeDict:
            curProfit = routeDict[route]["totalProfit"]
            if curProfit > profit:
                profit = curProfit
                bestRouteName = route
                bestRoute = routeDict[route]
        return bestRouteName, bestRoute
    
    def parse_info(self):
        if not self.route:
            return "No Route found for {} to {}".format(self.fromSystem.name, self.toSystem.name)
        result = ""
        stops = self.routeName.split(" -> ")
        previousProfit = 0
        for id, stop in enumerate(stops):
            result += stop + "\n"   # display stop name
            if id > 0:
                result += "  Profit: {}\n".format(previousProfit)
            if id < len(stops)-1:
                previousProfit = 0
                for item in self.route["items"][id]:
                    result += "   BUY {} x{} \n".format(item["itemName"], item["count"])
                    previousProfit += item["profit"]
        return result
                
    """
    Util functions
    """
    def construct_route(self, routeName: str, items, totalProfit, systemList):
        stationCount = len(routeName.split(" -> "))
        route = {
            "items" : items,
            "totalProfit" : totalProfit,
            "stations" : stationCount,
            "system_objs" : systemList
        }
        return route
    
    def create_copy_of_last_system(self, lastRouteName, lastRoute):
        stops = lastRouteName.split(" -> ")
        lastStation = stops[-1].split("/")[-1]

        # calculate next route
        lastSystem = lastRoute["system_objs"][-1].copy()   # get a copy of the last system_obj
        lastSystem.isolate_station(lastStation)

        return lastSystem
    

"""
Main classes
"""
class RoutePlanner:
    def __init__(self, curSystem: str, targetSystem: str, jumpCapacity, minRange=0):
        assert isinstance(jumpCapacity, int) or isinstance(jumpCapacity, float)
        self.system_route = []

        # run the planning
        coords = get_system_coord(targetSystem)
        if not coords:
            print("ERROR: Couldn't find target's coordinate!")
        coords = list(coords.values())

        curCoords = get_system_coord(curSystem)
        if not curCoords:
            print("ERROR: Couldn't find current coordinate!")
        curSystem = SystemInfo(curSystem, coords=curCoords)
        
        self.find_target_system(curSystem, targetSystem, coords, jumpCapacity)

    def find_target_system(self, curSystem, targetSystemName, targetCoord, jumpCapacity, latestNearby=[], excluded=[], goneBack=False):
        if goneBack and latestNearby:
            nearbys = latestNearby
        else:
            # append the current system into list
            self.system_route.append(curSystem)

            # get nearby reachable systems
            nearbys = get_systems_in_radius(curSystem.name, jumpCapacity, includeAnarchy=True)

        nearbyNames = [x["name"] for x in nearbys]
        curNames = [x.name for x in self.system_route]

        # if target is reachable, append and done, else find closest to target and run again
        if targetSystemName in nearbyNames:
            targetSystem = next((x for x in nearbys if x["name"] == targetSystemName), None)
            if targetSystem:
                self.system_route.append(SystemInfo(targetSystem["name"], coords=targetSystem["coords"], distance=targetSystem["distance"]))
            else:
                print("ERROR: Couldn't get Destination system!")
        else:
            # calculate distance and find where next stop should be
            distance = None
            newStop = None
            for system in nearbys:
                coord = list(system["coords"].values())
                curDist = math.dist (coord, targetCoord)
                if distance is None:
                    distance = curDist
                    newStop = system
                else:
                    if curDist < distance and system["name"] not in excluded:
                        distance = curDist
                        newStop = system
            if not newStop:
                print("ERROR: Can't find next stop!")   # there should always be at least itself in the return list, so error if dont have
                raise

            elif newStop["name"] in excluded:
                self.remove_system(newStop["name"]) # remove system from system_route
                # step back now
                if goneBack:
                    latestNearby = []   # if already gone back dont pass nearbys again
                self.find_target_system(self.system_route[-1], targetSystemName, targetCoord, jumpCapacity, latestNearby=latestNearby, excluded=excluded, goneBack=True)

            elif newStop in curNames:   # if the closest stop is already in the list (i.e itself), then remove from the list and step back
                excluded.append(newStop["name"])
                self.remove_system(newStop["name"])   # remove system from system_route
                if goneBack:
                    latestNearby = []   # if already gone back dont pass nearbys again
                self.find_target_system(self.system_route[-1], targetSystemName, targetCoord, jumpCapacity, latestNearby=latestNearby, excluded=excluded, goneBack=True)
            else:
                newSystem = SystemInfo(newStop["name"], coords=newStop["coords"], distance=newStop["distance"])
                self.find_target_system(newSystem, targetSystemName, targetCoord, jumpCapacity, latestNearby=latestNearby, excluded=excluded)

    """
    Util function
    """
    def remove_system(self, systemD):
        toDelName = systemD["name"]
        systemToDel = next((x for x in self.system_route if x.name == toDelName), None)
        if systemToDel:
            self.system_route.remove(systemToDel)
                

class TripPlanner:
    def __init__(self, curLocation: str, targetLocation: str, jumpCapacity, minHop: int=1, deviation=2, cargoSpace: int=8, minRange=0):
        # ensure input is correct
        assert isinstance(jumpCapacity, int) or isinstance(jumpCapacity, float)
        assert isinstance(deviation, int) or isinstance(deviation, float)
        assert isinstance(minRange, int) or isinstance(minRange, float)
        self.cargoSpace = cargoSpace
        self.jumpCapacity = jumpCapacity
        self.deviation = deviation

        # parse location first
        curSystem, curStation = self.location_parse(curLocation)
        targetSystem, targetStation = self.location_parse(targetLocation)
        
        # get neccessary stops
        self.routePlanner = RoutePlanner(curSystem, targetSystem, jumpCapacity, minRange=minRange)
        print("LOG: Route planned.")

        # embbed stations into first and last system and generate their infos
        firstSystem = self.routePlanner.system_route[0]
        lastSystem = self.routePlanner.system_route[-1]
        assert isinstance(firstSystem, SystemInfo)
        assert isinstance(lastSystem, SystemInfo)
        if curStation:
            firstSystem.stationToScan = [curStation]
        else:
            firstSystem.get_all_stationNames()
        if targetStation:
            lastSystem.stationToScan = [targetStation]
        else:
            lastSystem.get_all_stationNames()
        firstSystem.gather_station_infos()
        lastSystem.gather_station_infos()
        
        # proceed to calculate the plan
        self.routes = self.plan_trip(minHop)

        # print the results
        print("Final Result----------------------------------------")
        self.print_route(self.routes)

    def plan_trip(self, minHop):
        # sectioning route
        print("LOG: Sectioning route based on mininum hop.")
        filtered_system = self.filter_non_anarchy(self.routePlanner.system_route)
        system_sectioned = []
        if minHop <= 1:
            system_sectioned = [filtered_system]
        else:
            sectionLength = int(float(len(filtered_system))/minHop)
            # deal with situation if section length is shorter than 1
            if not sectionLength:
                sectionLength = 1
                minHop = len(filtered_system)
            for i in range(minHop):
                curRoute = filtered_system[i*sectionLength : (sectionLength*(i+1))+1]
                system_sectioned.append(curRoute)
        
        # loop and calculate their respective route
        plannedRoutes = []
        for id, section in enumerate(system_sectioned):
            print("LOG: Planning trade for section: {}".format(section))
            deviations = []

            if not section:
                continue

            # generate station data for start and end
            for system in [section[0], section[-1]]:
                if not system.stationToScan:
                    system.get_all_stationNames()
                    system.gather_station_infos()
                else:
                    if not system.stationInfos:
                        system.gather_station_infos()
            
            # gather deviations
            if len(section) > 2:
                print("LOG: Gathering in-betweens...")
                for system in section[1:-1]:
                    system.get_all_stationNames()
                    system.gather_station_infos()
                    deviations.append(system)
                print("LOG: Gathering deviations...")
                for system in section[1:-1]:
                    nearbys = get_systems_in_radius(system.name, radius=self.jumpCapacity*self.deviation)
                    curNames = [x.name for x in deviations] + [section[0].name, section[-1].name]
                    for systemD in nearbys:
                        if systemD["name"] not in curNames:
                            newSystem = SystemInfo(systemD["name"], systemD["coords"], systemD["distance"])
                            newSystem.get_all_stationNames()
                            newSystem.gather_station_infos()
                            deviations.append(newSystem)

            print("LOG: Calculating trade route for section...")
            newRoute = RouteInfo(section[0],section[-1], deviations, self.cargoSpace)
            print("LOG: Section calculated, printing...")
            self.print_route([newRoute])
            plannedRoutes.append(newRoute)

            # replace next section start with system of isolated station
            if id < len(system_sectioned)-2:
                newSystem = newRoute.create_copy_of_last_system(newRoute.routeName, newRoute.route)
                system_sectioned[id+1][0] = newSystem

        return plannedRoutes

    def print_route(self, routes):
        for route in routes:
            print(route.parse_info())

    """
    Util functions
    """
    def filter_non_anarchy(self, systems):
        result = []
        for system in systems:
            if not is_system_anarchy(system.name):
                result.append(system)
        return result
    
    # parse system and station from location i.e Gilya/Kendrick Enterprise
    def location_parse(self, location: str):
        splitted = location.split("/")
        system = splitted[0]
        station = ""
        if len(splitted) > 1:
            station = splitted[1]

        return system, station