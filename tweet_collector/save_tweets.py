#not neeeded anymore beacause get_tweets.py is directly connecting to MongoDB

import pandas as pd
import pymongo


df = pd.read_csv('tweets.csv')

# remove columns with dots and strange chars
for c in df:
    if '.' in c or '#' in c:
        del df[c]

# create a list of dictionaries
r = df.to_dict(orient='records')

# connect to local MongoDB
client = pymongo.MongoClient()
db = client.tweets #use pokemon database

# write to a collection called pokemon_data
db.tweets_data.insert_many(r)

# read
for x in db.tweets_data.find({'Name': {'$in': ['Pikachu', 'Bulbasaur']}
}):
    print(x)
