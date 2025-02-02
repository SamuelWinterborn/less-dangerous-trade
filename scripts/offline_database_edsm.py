import os
import ijson
import json
import gzip
import shutil

from . import offline_database as od

urls = {
    "system_coords_url" : "	https://www.edsm.net/dump/systemsWithCoordinates.json.gz",
    "populated_system_url" : "https://www.edsm.net/dump/systemsPopulated.json.gz",
    "stations_url" : "	https://www.edsm.net/dump/stations.json.gz"
}
offline_database_path_raw = os.path.abspath("./database_raw_edsm")

class OfflineDatabase_EDSM(od.OfflineDatabase):
    def __init__(self):
        self.urlDict = urls
        od.OfflineDatabase.__init__(self, offline_database_path_raw)

    def update_populated_systems(self):
        url = self.urlDict["populated_system_url"]
        file = os.path.join(self.rawDatasetPath, self.file_from_url(url))

        # Download the file if doesnt exists
        if not os.path.isfile(file):
            self.download_file(url)
        
        # if downloaded, then extract it
        self.extract_populated_systems(file)

        # after done, then delete the downloaded raw file
        os.remove(file)

    def update_system_coords(self):
        url = self.urlDict["system_coords_url"]
        file = os.path.join(self.rawDatasetPath, self.file_from_url(url))

        # Download the file if doesnt exists
        if not os.path.isfile(file):
            self.download_file(url)
        
        # if downloaded, then extract it
        self.extract_system_coords(file)

        # after done, then delete the downloaded raw file
        os.remove(file)

    def update_stations(self):
        url = self.urlDict["stations_url"]
        file = os.path.join(self.rawDatasetPath, self.file_from_url(url))

        # Download the file if doesnt exists
        if not os.path.isfile(file):
            self.download_file(url)
        
        # if downloaded, then extract it
        self.extract_stations(file)

        # after done, then delete the downloaded raw file
        os.remove(file)

    def extract_populated_systems(self, file):
        unzip_file = os.path.splitext(file)[0]

        # unzip gz file first
        with gzip.open(file, 'rb') as f_in:
            with open(unzip_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        dataList = []
        with open(unzip_file, 'rb') as input_file:
            for record in ijson.items(input_file, "item"):
                newData = {
                    "id" : record['id'],
                    "name" : record['name'],
                }

                stationList = []
                for station in record['stations']:
                    if (station['haveMarket']):
                        newStationData = {
                            "id" : station['id'],
                            "marketId" : station['marketId'],
                            "type" : station['type'],
                            "name" : station['name']
                        }
                        stationList.append(newStationData)
                
                if (stationList):
                    newData['stations'] = stationList
                    dataList.append(newData)
            
        with open(self.populated_system_file, 'w', encoding ='utf8') as json_file: 
            json.dump(dataList, json_file) 

    def extract_system_coords(self, file):
        unzip_file = os.path.splitext(file)[0]

        # unzip gz file first
        with gzip.open(file, 'rb') as f_in:
            with open(unzip_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        with open(unzip_file, 'rb') as input_file:
            dataList = []
            maxCount = 1048576
            id = 0
            for record in ijson.items(input_file, "item"):
                newData = {
                    "id" : record['id'],
                    "name" : record['name']
                }

                origCoords = record['coords']
                coords = {}
                for elem in origCoords:
                    coords[elem] = float(origCoords[elem])
                newData["coords"] = coords

                dataList.append(newData)
                
                if len(dataList) >= maxCount:
                    self.save_system_coords(dataList, id)
                    dataList = []
                    id += 1

            if dataList:
                self.save_system_coords(dataList, id)

    def extract_stations(self, file):
        unzip_file = os.path.splitext(file)[0]

        # unzip gz file first
        with gzip.open(file, 'rb') as f_in:
            with open(unzip_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        with open(unzip_file, 'rb') as input_file:
            dataList = []
            maxCount = 4096
            id = 0
            for record in ijson.items(input_file, "item"):
                # skip record if no market
                if not record['haveMarket']:
                    continue

                newData = {
                    "id" : record['id'],
                    "name" : record['name'],
                    "type" : record['type'],
                    "haveShipyard" : record['haveShipyard'],
                    "commodities" : record['commodities']
                }
                dataList.append(newData)

                if len(dataList) >= maxCount:
                    self.save_station_market(dataList, id)
                    dataList = []
                    id += 1
                
            if dataList:
                self.save_station_market(dataList, id)

    def save_system_coords(self, list, id):
        self.ensure_directory(self.system_coords_path)
        file = os.path.join(self.system_coords_path, "system_coords_{}.json".format(id))
        with open(file, 'w', encoding ='utf8') as json_file: 
            json.dump(list, json_file)

    def save_station_market(self, list, id):
        self.ensure_directory(self.station_market_path)
        file = os.path.join(self.station_market_path, "station_market_{}.json".format(id))
        with open(file, 'w', encoding ='utf8') as json_file: 
            json.dump(list, json_file)