import os
import shutil
import requests
import asyncio
import time
import math
import pandas as pd

offline_database_path = os.path.abspath("./database")
populated_system_file = os.path.join(offline_database_path, "populated_system.json")
station_market_path = os.path.join(offline_database_path, "station_market")
system_coords_path = os.path.join(offline_database_path, "system_coords")

class SystemCoordsIterator:
    def __init__(self):
        self._sequence = os.listdir(system_coords_path)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._sequence):
            fName = self._sequence[self._index]
            file = os.path.join(system_coords_path, fName)
            df = pd.read_json(file)
            self._index += 1
            return df
        else:
            raise StopIteration
        
class StationMarketIterator:
    def __init__(self):
        self._sequence = os.listdir(station_market_path)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._sequence):
            fName = self._sequence[self._index]
            file = os.path.join(station_market_path, fName)
            df = pd.read_json(file)
            self._index += 1
            return df
        else:
            raise StopIteration
        
# file manager class for syncing and managing database files
class OfflineDatabase:
    def __init__(self, rawPath):
        self.datasetPath = offline_database_path
        self.rawDatasetPath = rawPath
        self.populated_system_file = populated_system_file
        self.station_market_path = station_market_path
        self.system_coords_path = system_coords_path
        self.ensure_directories([self.datasetPath, self.rawDatasetPath, self.system_coords_path])
        self.isValid = self.ensure_files()
        
    def ensure_directories(self, pathList):
        for path in pathList:
            self.ensure_directory(path)

    def ensure_directory(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)

    def ensure_files(self):
        result = True
        if not os.path.isfile(self.populated_system_file):
            result = False
            print ("Error: Populated system not found, please check Readme.md for how to obtain it.")

        if len(os.listdir(self.station_market_path)) <= 0:
            result = False
            print ("Error: Station Market not found, please check Readme.md for how to obtain it.")

        if len(os.listdir(self.system_coords_path)) <= 0:
            result = False
            print ("Error: System Coords not found, please check Readme.md for how to obtain it.")
        return result

    def get_populated_systems(self):
        if not os.path.isfile(self.populated_system_file):
            return (None, None)
        return True, pd.read_json(self.populated_system_file)
    
    def get_station_market(self):
        return StationMarketIterator()
    
    def get_system_coords(self):
        return SystemCoordsIterator()

    def download_file(self, url):
        local_filename = self.file_from_url(url)
        path = os.path.join(self.rawDatasetPath, local_filename)
        print("LOG: Downloading {} to {}".format(url, path))
        with requests.get(url, stream=True) as r:
            with open(path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return local_filename
    
    def get_all_filenames(self, urlsDict):
        filenames = []
        for key in urlsDict:
            filenames.append(self.file_from_url(urlsDict[key]))
        return filenames

    def file_from_url(self, url):
        filename = url.split('/')[-1]
        return filename
    
OD = OfflineDatabase(offline_database_path)

# returns system coordinate value
def get_system_coord(systemName):
    if not systemName:
        print("ERROR: Need system name to get coordinate!")
        return None
    
    coords = None
    systemCoords = OD.get_system_coords()
    for df in systemCoords:
        filteredDf = df[df["name"] == systemName]
        if len(filteredDf.index):
            coords = filteredDf.iloc[0]['coords']
            break
        
    if not coords:
        print("ERROR: Couldn't find system!")
        return None

    return coords

# returns true if system is anarchy
def is_system_anarchy(systemName):
    if not systemName:
        print("ERROR: Need system name to find if anarchy!")
        return None
    
    b_gotPopulatedSystem, populatedSystem = OD.get_populated_systems()

    if not b_gotPopulatedSystem:
        print("ERROR: Failed getting populated system!")
        return True
    
    filteredDf = populatedSystem[populatedSystem["name"] == systemName]
    if len(filteredDf.index):
        return False
    else:
        return True
    
# returns list of all systems in radius of a given system
def get_systems_in_radius(systemName, radius, coords=None, minRadius=None, includeAnarchy=False):
    if not systemName:
        print("ERROR: Need system name to find nearby!")
        raise
    
    if not coords:
        coords = get_system_coord(systemName)
    
    if not coords:
        print("ERROR: Could not find coordinate for origin!")
        raise

    originX = coords['x']
    originY = coords['y']
    originZ = coords['z']
    result = []
    systemCoords = OD.get_system_coords()
    for df in systemCoords:
        dfInRange = df[
            (df.coords.apply(lambda entry: entry['x'] >= originX - radius*0.5)) & 
            (df.coords.apply(lambda entry: entry['x'] <= originX + radius*0.5)) &
            (df.coords.apply(lambda entry: entry['y'] >= originY - radius*0.5)) & 
            (df.coords.apply(lambda entry: entry['y'] <= originY + radius*0.5)) &
            (df.coords.apply(lambda entry: entry['z'] >= originZ - radius*0.5)) & 
            (df.coords.apply(lambda entry: entry['z'] <= originZ + radius*0.5)) 
            ]
        
        if minRadius:
            dfInRange_filtered = dfInRange[
            (df.coords.apply(lambda entry: entry['x'] >= originX + minRadius*0.5)) & 
            (df.coords.apply(lambda entry: entry['x'] <= originX - minRadius*0.5)) &
            (df.coords.apply(lambda entry: entry['y'] >= originY + minRadius*0.5)) & 
            (df.coords.apply(lambda entry: entry['y'] <= originY - minRadius*0.5)) &
            (df.coords.apply(lambda entry: entry['z'] >= originZ + minRadius*0.5)) & 
            (df.coords.apply(lambda entry: entry['z'] <= originZ - minRadius*0.5)) 
            ]
            dfInRange = dfInRange_filtered

        for index, row in dfInRange.iterrows():
            if not includeAnarchy:
                if is_system_anarchy(row['name']):
                    continue

            result.append(
                {"name": row['name'], 
                    "coords": row['coords'], 
                    "distance": math.dist([originX, originY, originZ], [row['coords']['x'], row['coords']['y'], row['coords']['z']])
                }
                )

    return result

# returns list of all stations of the system
def get_stations(systemName, noPlanet=True):
    if not systemName:
        print("ERROR: Need system name to find stations!")
        return None
    
    b_gotPopulatedSystem, populatedSystem = OD.get_populated_systems()

    if not b_gotPopulatedSystem:
        print("ERROR: Failed getting populated system!")
        return None

    filteredDf = populatedSystem[populatedSystem["name"] == systemName]
    if not len(filteredDf.index):
        print("ERROR: Couldn't find system in PopulatedSystem!")
        return None
    
    systemEntry = filteredDf.iloc[0]
    stations = systemEntry['stations']
    
    if not stations:
        return None
    result = []
    for station in stations:
        if "name" not in station:
            continue
        if noPlanet:
            if "type" not in station:
                continue
            else:
                if station["type"] == "Odyssey Settlement" or "Planetary" in station["type"]:
                    continue
        result.append(station["name"])

    return result

# return station ID
def get_stationID(systemName, stationName):
    if not systemName:
        print("ERROR: Need system name to find stations!")
        return None
    
    b_gotPopulatedSystem, populatedSystem = OD.get_populated_systems()

    if not b_gotPopulatedSystem:
        print("ERROR: Failed getting populated system!")
        return None
    
    filteredDf = populatedSystem[populatedSystem["name"] == systemName]
    if not len(filteredDf.index):
        print("ERROR: Couldn't find system in PopulatedSystem!")
        return None
    
    systemEntry = filteredDf.iloc[0]
    stations = systemEntry['stations']
    
    if not stations:
        print("ERROR: Could not find station")
        return None
    
    for station in stations:
        if station['name'] == stationName:
            return station['id']

    print("ERROR: Could not find station")
    return None

# returns market data of a specific station
def get_market_data(systemName, stationName):
    if not systemName:
        print("ERROR: Need system name to find market!")
        return None
    if not stationName:
        print("ERROR: Need station name to find market!")
        return None
    
    station_id = get_stationID(systemName, stationName)

    if station_id == None:
        return None
    
    station_market = OD.get_station_market()
    b_foundEntry = False

    for df in station_market:
        filteredDf = df[df["id"] == station_id]
        if len(filteredDf.index):
            station_entry = filteredDf.iloc[0]
            b_foundEntry = True
            break
    
    if not b_foundEntry:
        print("ERROR: Could not find station market")
        return None

    return station_entry["commodities"]