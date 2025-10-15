import http.client
from typing import List, Dict

"""
An API adapter to retrieve data from reccobeats
"""

class reccobeats:
    def __init__(self):
        self.BaseURL = "https://api.reccobeats.com"
    
    def request(self, method: str, payload: str) -> str:
        """
        Adapter to make requests to the API
        
        Args:
            method: The type of API call
            payload: The input parameters of the API call
        
        Returns:
            Dictionary for the Returned JSON
        """
        conn = http.client.HTTPSConnection("api.reccobeats.com")
        header = {
            'Accept': 'application/json'
        }
        conn.request("GET", f"/v1/{method}?ids={payload}", headers=header)
        res = conn.getresponse()
        data = res.read()
        return eval(data.decode("utf-8"))

    def getmany_Audio_Features(self, tracks: List) -> str:
        """
        Wrapper to perform correct API call for audio features
        
        Args:
            tracks: A list of all the tracks to get Audio features for

        Returns:
            Dictionary of Returned JSON
        """
        payload = ""
        for i in tracks:
            payload = payload + i + ','
        
        return self.request("audio-features", payload[:-1])
    
    


