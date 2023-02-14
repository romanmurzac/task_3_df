import logging
import time
import json

from os import getenv
from google.cloud import pubsub_v1
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)

FUNCTION_REGION = getenv("FUNCTION_REGION")
PROJECT_ID = getenv("PROJECT_ID")
OUTPUT_TABLE = getenv("OUTPUT_TABLE")
OUTPUT_DATASET = getenv("OUTPUT_DATASET")
TOPIC_NAME = getenv("TOPIC_NAME")


class PubSubPublisher:
    def __init__(self, publisher: pubsub_v1.PublisherClient,
                 project_id: str,
                 topic_id: str, ):
        self._publisher = publisher
        self._topic_path = publisher.topic_path(project_id, topic_id)

    def publish(self, data: bytes) -> bool:
        try:
            future = self._publisher.publish(self._topic_path,
                                             data)
            try:
                future.result()
                logging.info("Successfully published to topic")
                return True
            except RuntimeError as err:
                logging.error("An error occurred during "
                              "publishing the message",
                              str(err))
                return False
        except Exception as err:
            logging.error(f"Unexpected error: {str(err)}")
            return False


def convert_timestamp_to_sql_date_time(value):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))


def store_data_into_bq(dataset, timestamp, event):
    try:
        query = f"INSERT INTO `{dataset}` VALUES ('{timestamp}', '{event}')"
        bq_client = bigquery.Client()
        query_job = bq_client.query(query=query)
        query_job.result()
        logging.info(f"Query results loaded to the {dataset}")
    except AttributeError as error:
        logging.error(f"Query job could not be completed: {error}")


def store_data_into_pubsub(event):
    ps_client = pubsub_v1.PublisherClient()
    ps_object = PubSubPublisher(ps_client, PROJECT_ID, TOPIC_NAME)
    try:
        data = bytes(event, 'utf-8')
        ps_object.publish(data)
        logging.info(f"Message was published to the {TOPIC_NAME}")
    except AttributeError as error:
        logging.error(f"Publishing not be completed: {error}")


def main(request):
    logging.info("Request: %s", request)

    if request.method == "POST":
        event: str
        try:
            event = json.dumps(request.json)
        except TypeError as error:
            return {"error": f"Function only works with JSON. Error: {error}"}, 415, \
                   {'Content-Type': 'application/json; charset=utf-8'}

        timestamp = time.time()
        table = f"{PROJECT_ID}.{OUTPUT_DATASET}.{OUTPUT_TABLE}"
        store_data_into_bq(table,
                           convert_timestamp_to_sql_date_time(timestamp),
                           event)

        store_data_into_pubsub(event)

        return "", 204

    return {"error": f"{request.method} method is not supported"}, 500, \
           {'Content-Type': 'application/json; charset=utf-8'}
