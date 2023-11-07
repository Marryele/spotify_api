#%%
import requests
from urllib.parse import urlencode
import base64
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

#credentials from app spotify
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

refresh_token = os.getenv("REFRESH_TOKEN")

pg_user = os.getenv("PG_USER")
pg_password = os.getenv("PG_PASSWORD")
pg_database = os.getenv("PG_DATABASE")


def token_refresh():
    encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")
    token_headers = {
    "Authorization": "Basic " + encoded_credentials,
    "Content-Type": "application/x-www-form-urlencoded"
    }
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    }
    response = requests.post(token_url, data=data, headers=token_headers)
    if response.status_code == 200:
        new_token_data = response.json()
        new_access_token = new_token_data['access_token']
        return new_access_token
    else:
        print(f'Error: {response.status_code} - {response.text}')

token = token_refresh()

#function to call the api spotify
def call_spotify_api(url, parameters,token):
    headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
    }
    result = requests.get(url, params=parameters, headers=headers)
    if result.status_code == 200:
        return result.json()
    elif result.status_code == 401:
        token = token_refresh()
        headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
        }
        result = requests.get(url, params=parameters, headers=headers)
        return result.json()
    else:
        print(f'Error: {result.status_code} - {result.text}')

#%%
# Function to write on my postgree database
def write_postgree(table_name,df):
    engine = create_engine(f'postgresql+psycopg2://{pg_user}:{pg_password}@localhost/{pg_database}')
    table_name = table_name
    #I choose replace method because of this application
    df.to_sql(table_name, engine, if_exists='replace', index=False)

# Calling all the episodes with Data Hackers term on search

user_params_shows = {
    "q": "Data Hackers",
    "type": "show",
    "limit":50
}
url_search = "https://api.spotify.com/v1/search"
user_search = call_spotify_api(url_search,user_params_shows,token)

#creating the table with the 50 results
table_shows = pd.json_normalize(user_search['shows']['items'])

#filtering columns to the final table
table_5 = table_shows[["name","description","id","total_episodes"]]

#%%

#write_postgree("Podcasts list",table_5)

#get the id of the Data Hackers show to get all the episodes 
show_id = table_5.query("name == 'Data Hackers'").loc[0,'id']

url_get_episodes = f"https://api.spotify.com/v1/shows/{show_id}/episodes"
offset = 0
url_parameters = {"limit": 50, "offset": offset}
episodes = call_spotify_api(url_get_episodes,url_parameters,token)
table_episodes = pd.json_normalize(episodes['items'])
while episodes['next'] is not None:
    offset = offset+50
    url_parameters = {"limit": 50, "offset": offset}
    episodes = call_spotify_api(url_get_episodes,url_parameters,token)
    table_episodes = table_episodes.append(pd.json_normalize(episodes['items']))


#All the episodes selecting the columns
table_6 = table_episodes[['id','name','description','release_date','duration_ms','language','explicit','type']]
#write_postgree("Data Hackers episodes",table_6)
#Search for episodes in the column description by "Grupo Boticário"
table_7 = table_6[table_6['description'].str.contains('Grupo Boticário', case=False)]
#write_postgree("Data Hackers - Boticário episodes",table_7)

# %%

import pandas as pd
from deltalake import DeltaTable
from deltalake.writer import write_deltalake
import deltalake
# %%
table_episodes.to_parquet("/lake/parquet_file", partition_cols = ['release_date'])
#%%
write_deltalake('/lake/delta_table', table_episodes,
                description= 'dataframe created to demonstraction of Delta table with Pandas',
                partition_by= ['release_date'])
# %%
dataframe = DeltaTable('/lake/delta_table').to_pandas()
# dataframe.set_index('id', inplace = True)
dataframe.head()
# %%
#ESCREVER NA AWS
aws_keys = {"AWS_ACCESS_KEY_ID": "access key id",
                   "AWS_SECRET_ACCESS_KEY":"secret access key",
                   "AWS_REGION":"us-east-1",
                   'AWS_S3_ALLOW_UNSAFE_RENAME': 'true'}
write_deltalake('s3://bucket-name/folder',
                table_episodes,
                storage_options = aws_keys)

DeltaTable('s3://bucket-name/folder',
           storage_options = aws_keys)