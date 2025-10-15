import requests
import json
from typing import List, Dict

"""
An API adapter to retrieve data from reccobeats
"""

class reccobeats:
    def __init__(self):
        self.BaseURL = "https://api.reccobeats.com"

    def getmany_Audio_Features(self, tracks: List[str]) -> List[Dict]:
        """
        Wrapper to perform correct API call for audio features
        
        Args:
            tracks: A list of all the tracks to get Audio features for

        Returns:
            A list of dictionaries of audio features
        """
        if not tracks:
            return []
            
        payload = ",".join(tracks)
        url = f"{self.BaseURL}/v1/audio-features"
        headers = {'Accept': 'application/json'}
        params = {'ids': payload}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            # The API is expected to return a dictionary with a 'content' key.
            if isinstance(data, dict) and 'content' in data:
                return data['content']
            else:
                print(f"Unexpected response format from reccobeats API: {data}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from reccobeats API: {e}")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from reccobeats API. Response: {response.text}")
            return []
