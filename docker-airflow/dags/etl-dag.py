##### 1. Import modules #####
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import time
import pymongo
from sqlalchemy import create_engine
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sa = SentimentIntensityAnalyzer()
def sentiment(x):
    return sa.polarity_scores(x)

##### 2. Define default arguments #####
default_args = {
    "owner": "airflow",
    # depends_on_past determines whether we run a DAG if a past DAG has failed
    "depends_on_past": False,
    "start_date": datetime(2020, 4, 6),
    "email": ["your_mail_adress@mail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    # 'end_date': datetime(2016, 1, 1),
}


##### 3. Instantiate DAG #####
dag = DAG("etl", default_args=default_args, schedule_interval=timedelta(minutes=1))


##### 4. Create Tasks #####
# Establish the connection to mongodb
conn = 'mongodb'
client = pymongo.MongoClient(conn)
db = client.tweets
collection = db.tweetcollection

# We define the extract function
def extract():
    tweets = collection.find().sort("_id", pymongo.DESCENDING).limit(1)
    if tweets:
        return tweets[0]
    return ""

# Instantiate Faker
#faker = Faker()

# We define the transform function
def transform(**context):
    extract_connection = context['task_instance']
    tweet = extract_connection.xcom_pull(task_ids="extract")
    sentiment_tweet = sentiment(tweet['text'])['compound']
    logging.critical(f'\n\n\nTransform \n{tweet} \n {sentiment_tweet}')
    return (tweet, sentiment_tweet)

# Establish a connection to Postgres
engine = None
while not engine:
    try:
        engine = create_engine("postgres://postgres:1234@postgres:5432")
    except:
        continue

engine.execute('''CREATE TABLE IF NOT EXISTS tweets (
    name TEXT,
    tweet TEXT,
    sentiment NUMERIC
);
''')

# We define the load function
def load(**context):
    extract_connection = context['task_instance']
    tweet, sentiment_tweet = extract_connection.xcom_pull(task_ids="transform")
    engine.execute(f"""INSERT INTO tweets VALUES ('{tweet["username"]}','{tweet["text"]}', '{sentiment_tweet}');""")


# Create the extract task
extract = PythonOperator(task_id='extract', python_callable=extract, dag=dag)

# Create the transform task
transform = PythonOperator(task_id='transform', python_callable=transform,
                           provide_context=True, dag=dag)

# Create the load task
load = PythonOperator(task_id='load', python_callable=load,
                      provide_context=True, dag=dag)


##### 5. Set up dependencies #####
extract >> transform >> load
