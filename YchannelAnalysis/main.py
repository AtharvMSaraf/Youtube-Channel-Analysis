
from googleapiclient.discovery import build
from IPython.display import JSON
import re
import requests
import pandas as pd

api_Key = 'AIzaSyBNY_LEltaXSwC6kT92j9AwT1Rtn1k4gzs'


def get_youtube_channel_id(youtube_url):
    # Standard channel URL pattern
    standard_channel_pattern = r"youtube\.com/channel/([A-Za-z0-9_-]+)"
    match = re.search(standard_channel_pattern, youtube_url)
    if match:
        return match.group(1)

    # Custom URL or handle pattern
    custom_url_pattern = r"youtube\.com/(user|c|@)([A-Za-z0-9_-]+)"
    match = re.search(custom_url_pattern, youtube_url)
    if match:
        custom_name = match.group(2)
        api_key = api_Key
        
        # Construct the appropriate API URL based on the type
        if match.group(1) == '@':
            # Use the search endpoint for handle
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={custom_name}&key={api_key}"
        else:
            # Use the channels endpoint for custom URLs
            url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forUsername={custom_name}&key={api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                return data['items'][0]['id']
            else:
                print("No channel found for this custom name.")
        else:
            print("Error fetching data from YouTube API:", response.status_code)
    return None


def get_channel_stats(youtube, channel_id):

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()

    all_channel_data = []

    for item in response['items']:
        data = {
            'channelName': item['snippet']['title'],
            'subscriberCount': item['statistics']['subscriberCount'],
            'viewCount': item['statistics']['viewCount'],
            'playlistID': item['contentDetails']['relatedPlaylists']['uploads'],
            'videoCount': item['statistics']['videoCount']
        }

        all_channel_data.append(data)
    return(pd.DataFrame(all_channel_data))

def get_videoIDs(youtube,df):
    all_video_ids = []
    for playlistid in df['playlistID']:    
        request = youtube.playlistItems().list(
            part="snippet, contentDetails",
            playlistId = playlistid,
            maxResults = 50
        )
        response = request.execute()
        video_ids = []
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
        next_page_token = response.get('nextPageToken')
        while next_page_token is not None:
            request = youtube.playlistItems().list(
                part="snippet, contentDetails",
                playlistId = playlistid,
                maxResults = 50,
                pageToken = next_page_token
            )
            response = request.execute()

            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            next_page_token = response.get('nextPageToken')    
    return video_ids

def get_video_details(youtube,video_ID):

    all_video_info = []

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_ID[0:6]
    )
    response = request.execute()

    for video in response['items']:
        stats_to_keep = {'snippet': ['channelTitle', 'title','description','tags', 'publishedAt'],
                         'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                         'contentDetails': ['duration', 'defination', 'caption']
                         }
        
        video_info = {}
        video_info['video_id'] = video['id']
        
        for k in stats_to_keep.keys():
            for v in stats_to_keep[k]:
                try:
                    video_info[v] = video[k][v]
                except:
                    video_info[v] = None

        all_video_info.append(video_info)
    return(pd.DataFrame(all_video_info))

def data_prepro(df):

    # print(df.isnull().sum())
    # print(df.dtypes)
    numerical_columns = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
    df[numerical_columns] = df[numerical_columns].apply(pd.to_numeric,axis = 1)
    print(df.dtypes)
if __name__ == "__main__":
    api_service_name = "youtube"
    api_version = "v3"

    # Get credentials and create an API client
    youtube = build(
    api_service_name, api_version, developerKey=api_Key)


    # Example usage:
    # youtube_url = input("Paste the URL of the channel of intrest")
    youtube_url = "https://www.youtube.com/@theyogainstituteofficial"
    channel_id = get_youtube_channel_id(youtube_url)
    if channel_id:
       df = get_channel_stats(youtube, channel_id['channelId'])
       video_ID = get_videoIDs(youtube,df)
       video_detail_df = get_video_details(youtube,video_ID)
       final_df = data_prepro(video_detail_df)
    else:
        print("Channel ID not found.")