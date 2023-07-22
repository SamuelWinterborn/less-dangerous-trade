import requests

parse_dict = {
    "+" : "%2B",
}

def url_parse(url):
    result = ""
    for x in url:
        if x in parse_dict:
            result += parse_dict[x]
        else:
            result += x
    return result

def api_call(url):
    url = url_parse(url)
    response = requests.get(url)
    return response.json()


# returns system coordinate value
def get_system_coord(systemName):
    if not systemName:
        print("ERROR: Need system name to get coordinate!")
        return None
    
    url = "https://www.edsm.net/api-v1/system?systemName={}&showCoordinates=1".format(systemName)
    response = api_call(url)

    if not response:
        print("ERROR: Couldn't find system!")
        return None
    if "coords" not in response:
        print("Error: Couldn't get coordinate! Try check on EDSM's site?")
        return None
    
    return response["coords"]

# returns true if system is anarchy
def is_system_anarchy(systemName):
    if not systemName:
        print("ERROR: Need system name to find if anarchy!")
        return None
    
    url = "https://www.edsm.net/api-v1/system?systemName={}&showInformation=1".format(systemName)
    response = api_call(url)

    if not response:
        print("ERROR: Couldn't find system for checking anarchy!")
        return True
    if "information" not in response:
        print("Error: Couldn't get Info! Try check on EDSM's site?")
        return True

    if response["information"]:
        return False
    else:
        return True

# returns list of all systems in radius of a given system
def get_systems_in_radius(systemName, radius, coords=None, minRadius=None, includeAnarchy=False):
    if not systemName:
        print("ERROR: Need system name to find nearby!")
        raise
    
    url = "https://www.edsm.net/api-v1/sphere-systems?systemName={}&radius={}&showCoordinates=1".format(systemName, radius)
    if coords:
        if len(coords) == 3:
            url = "https://www.edsm.net/api-v1/sphere-systems?x={}&y={}&z={}&radius={}&showCoordinates=1".format(coords['x'], coords['y'], coords['z'], radius)
    if minRadius:
        url += "&minRadius={}".format(minRadius)
    response = api_call(url)

    if not response:
        print("ERROR: Couldn't find system {} and/or nearby!".format(systemName))
        return [{"name": systemName, "coords": {"x": 0, "y": 0, "z": 0}, "distance": 0}]   # return self
    
    result = []
    for system in response:
        if "name" not in system or "distance" not in system or "coords" not in system:
            continue
        if not includeAnarchy:
            if is_system_anarchy(system["name"]):
                continue
        result.append(system)

    return result

# returns list of all stations of the system
def get_stations(systemName, noPlanet=True):
    if not systemName:
        print("ERROR: Need system name to find stations!")
        return None
    
    url = "https://www.edsm.net/api-system-v1/stations?systemName={}".format(systemName)
    response = api_call(url)

    if not response:
        print("ERROR: Couldn't find system and/or its station!")
        return None
    if "stations" not in response:
        print("ERROR: Couldn't find stations!")
        return None
    
    if not response["stations"]:
        return None
    result = []
    for station in response["stations"]:
        if "name" not in station:
            continue
        if noPlanet:
            if "type" not in station:
                continue
            else:
                if station["type"] == "Odyssey Settlement" or "Planetary" in station["type"] or not station["haveMarket"]:
                    continue
        result.append(station["name"])

    return result

# returns market data of a specific station
def get_market_data(systemName, stationName):
    if not systemName:
        print("ERROR: Need system name to find market!")
        return None
    if not stationName:
        print("ERROR: Need station name to find market!")
        return None
    
    url = "https://www.edsm.net/api-system-v1/stations/market?systemName={}&stationName={}".format(systemName, stationName)
    response = api_call(url)

    if not response:
        print("ERROR: Couldn't find system and/or its station and/or the market!")
        return None
    if "commodities" not in response:
        print("ERROR: No commodities found!")
        return None
    
    return response["commodities"]