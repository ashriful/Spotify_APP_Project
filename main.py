#Shout out to drshey
#https://github.com/drshrey/spotify-flask-auth-example

# Import All Neccesary Modules 
import json
from flask import Flask, request, redirect, g, render_template
import requests
import base64
import urllib
import urllib.parse
import pandas as pd
from pandas.io.json import json_normalize

# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response. 


app = Flask(__name__)

#  Client Keys
CLIENT_ID = "24c3f8d05a4b499886011a488ac313e5"
CLIENT_SECRET = "146c0bdbe3e7408b868ca32e0419ddc8"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters 
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8888
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)

# Modify Scope to Add in for other functions
SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# List parameters to feed the Auth arguement
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}


@app.route("/")
def index():
    # Authorization
    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key,val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    temp1 = CLIENT_ID + ":"+ CLIENT_SECRET
    temp2 = temp1.encode('utf-8','strict')
    HEADER_64 = base64.standard_b64encode(temp2)
    PARAMS = {'grant_type':'client_credentials'}				# Requested by Spotify for this particular authorization format
    AUTH_HEADERS = {'Authorization':b'Basic '+HEADER_64}
    r = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=AUTH_HEADERS)

    # Tokens are Returned to Application
    response_data = json.loads(r.content)
    access_token = response_data['access_token']
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    # Follow link: https://developer.spotify.com/web-api/get-current-users-profile/
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)
   
 
    # Get user playlist data
    # Follow link: https://developer.spotify.com/web-api/get-list-users-playlists/
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Pick playlist from playlist_data 
    # FIX THIS. IT ONLY DOES THE FIRST PLAYLIST
    href_playlist = playlist_data['items'][0]['id']

    # Grab tracks from playlist 
    # Follow link: https://developer.spotify.com/web-api/get-playlist/
    playlist_track_api_endpoint =  "{}/playlists/{}".format(profile_data["href"],href_playlist)
    playlists_track_response = requests.get(playlist_track_api_endpoint, headers=authorization_header)
    playlist_track_data = json.loads(playlists_track_response.text) 

    # Create list of track id's using for loop
    track_names= []
    track_id_dict = []

    for items in tracks:
       track_names.append(items['track']['name'])
       track_id_dict.append(items['track']['id'])

    # Add commas to input into request
    track_id = ",".join(track_id_dict)

    # Find Track Information from Track ID's
    # Follow link: https://developer.spotify.com/web-api/get-several-audio-features/ 
    track_features_endpoint =  "https://api.spotify.com/v1/audio-features/?ids={}".format(track_id)
    track_features_response = requests.get(track_features_endpoint, headers=authorization_header)
    track_features = json.loads(track_features_response.text) 

    # Make Data Frame with Track Features 

    d = []
    for feature in track_features['audio_features']:
        d.append(feature)
    df = pd.DataFrame(d)

    # Manipulate data frame to divide playlist by energy 
    # Low energy make it for from low to high 
    # High energy make it high to low 
    # Combine into one list 

    # Divide playlist by energy and ascend
    first_half = df[df['energy'] <= 0.7]
    list1= first_half.sort_values(by=['tempo'], ascending = True)
    id_list1 = list1['id'].tolist()

    # Divide playlist by energy and descend 
    second_half = df[df['energy'] > 0.7]
    list2= second_half.sort_values(by=['tempo'],ascending = False)
    id_list2 = list2['id'].tolist()

    # Combine the lists and add comma for input
    id_list_combo = id_list1 + id_list2
    id_list = ",".join(id_list_combo)

    # Check what the audio features of the new list is 
    id_list_features_endpoint =  "https://api.spotify.com/v1/audio-features/?ids={}".format(id_list)
    id_list_features_response = requests.get(id_list_features_endpoint, headers=authorization_header)
    id_list_features = json.loads(id_list_features_response.text) 

    # Name playlist
    # CHANGE THIS. TAKE IN USER INPUT
    name_playlist = json.dumps({
        'name' : "Math"
    })
    content_type = {
    "Authorization":"Bearer {}".format(access_token),
    "Content-Type": "application/json"
    }

    # Create playlist 
    # Follow link: https://developer.spotify.com/web-api/create-playlist/
    create_playlist_endpoint = "{}/playlists".format(profile_data["href"])
    create_playlist_response = requests.post(create_playlist_endpoint, data = create_playlist_data, headers= content_type)
    create_playlist = json.loads(create_playlist_response.text) 


    # In order to add our new arranged tracks to the new playlist we need to format 

    # Make list of track uri's and format them for the input 
    TRACK_URI_LIST = []
    for track_id in id_list:
       TRACK_URI_LIST.append("spotify%3Atrack%3A{}".format(track_id))
       TRACK_URI = ",".join(TRACK_URI)

    # Add tracks to the playlist 
    # Follow link: https://developer.spotify.com/web-api/create-playlist/
    add_tracks_playlist_endpoint = "{}/tracks?uris={}".format(create_playlist['href'],TRACK_URI)
    add_tracks_playlist = requests.post(add_tracks_playlist_endpoint, headers= authorization_header)
    add_tracks_playlist_test = add_tracks_playlist.status_code

    
    return render_template("index.html",sorted_array= add_tracks_playlist_test)

if __name__ == "__main__":
   app.run(debug=True,port=PORT)


