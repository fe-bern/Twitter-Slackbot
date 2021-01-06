import pymongo
import time
from sqlalchemy import create_engine
import logging
import config
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sa = SentimentIntensityAnalyzer()


def sentiment(x):
    return sa.polarity_scores(x)


conn = "mongodb"
client = pymongo.MongoClient(conn)
db = client.tweets
collection = db.tweetcollection

user=config.user
password=config.password
host=config.host

engine = None
while not engine:
    try:
        engine = create_engine(f"postgres://{user}:{password}@{host}:5432")
    except:
        continue

engine.execute(
    """CREATE TABLE IF NOT EXISTS tweets (
    name TEXT,
    tweet TEXT,
    compound FLOAT
);
"""
)


def extract():
    tweets = list(collection.find())
    if tweets:
        return tweets
    return ""


def transform(tweet_text):
    return sentiment(tweet_text)["compound"]


def load(tweet, sentiment_tweet):
    engine.execute(
        f"""INSERT INTO tweets VALUES ('{tweet["username"]}','{tweet["text"]}', '{sentiment_tweet}');"""
    )


while True:
    tweet = extract()
    sentiment_tweet = transform(tweet)
    logging.critical("\n\nsentiment_tweet")
    load(tweet, sentiment_tweet)
    logging.critical("\n\nTRANSFORMED TWEET LOADED!")
    time.sleep(10)
