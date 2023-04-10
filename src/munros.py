import json
import logging
import os
import re
import time
from typing import Any

import boto3
import botocore
import requests
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    logging.info(
        f"Beginning execution of pocket.py with Lambda event: {str(event)} and Lambda context: {str(context)}"
    )

    client_id = "17865"
    secrets_manager_client: boto3.client = boto3.client(
        service_name="secretsmanager",
        region_name="eu-west-2",
    )
    client_secret: str = secrets_manager_client.get_secret_value(
        SecretId="strava-client-secret"
    )["SecretString"]

    refresh_token: str = secrets_manager_client.get_secret_value(
        SecretId="strava-refresh-token"
    )["SecretString"]

    refresh_response = requests.post(
        "https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )

    refreshed_access_token = refresh_response.json()["access_token"]
    new_refresh_token = refresh_response.json()["refresh_token"]

    secrets_manager_client.update_secret(
        SecretId="strava-refresh-token",
        SecretString=new_refresh_token,
    )

    munro_activity_ids = fetch_munro_activity_ids(
        page_number=1, access_token=refreshed_access_token
    )
    activities = []

    for munro_activity_id in munro_activity_ids:
        activities.append(fetch_activity(munro_activity_id, refreshed_access_token))

    bucket = "munros.blairnangle.com"
    latest_file_name = "munros.json"

    with open(f"/tmp/{latest_file_name}", "w") as f:
        json.dump(activities, f)

    try:
        s3_client.head_object(Bucket=bucket, Key=latest_file_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logging.info(
                f"File {latest_file_name} does not exist in bucket {bucket}. This is expected on the first execution."
            )
    else:
        copy_file(
            existing_file=latest_file_name,
            new_file=f"munros-{time.strftime('%Y-%m-%d')}.json",
            bucket=bucket,
        )

    upload_file(
        file_name=f"/tmp/{latest_file_name}",
        bucket=bucket,
        object_name=latest_file_name,
    )


def filter_munros(activity_list: list[dict[str]]) -> list[int]:
    result = []
    for activity in activity_list:
        if re.search(r"#munros", activity["name"].lower()):
            result.append(activity["id"])

    return result


def fetch_munro_activity_ids(page_number: int, access_token: str) -> list[int]:
    munro_activity_ids = []
    page_of_summaries = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?per_page=200&page={page_number}",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    if page_of_summaries:
        munro_activity_ids += filter_munros(page_of_summaries)
        munro_activity_ids += fetch_munro_activity_ids(page_number + 1, access_token)

    return munro_activity_ids


def fetch_activity(activity_id: str, access_token: str) -> dict[str, Any]:
    activity = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    return {
        "id": activity["id"],
        "name": activity["name"],
        "description": activity["description"],
        "distance": activity["distance"],
        "moving_time": activity["moving_time"],
        "elapsed_time": activity["elapsed_time"],
        "total_elevation_gain": activity["total_elevation_gain"],
        "elev_high": activity["elev_high"],
        "elev_low": activity["elev_low"],
        "start_date": activity["start_date"],
        "start_date_local": activity["start_date_local"],
        "timezone": activity["timezone"],
    }


s3_client = boto3.client(service_name="s3")


def upload_file(file_name: str, bucket: str, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def copy_file(existing_file: str, new_file: str, bucket: str):
    s3_resource = boto3.resource("s3")
    try:
        s3_resource.Object(bucket, new_file).copy_from(
            CopySource=f"{bucket}/{existing_file}"
        )
    except ClientError as e:
        logging.error(e)
        return False
    return True
