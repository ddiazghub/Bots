#!/usr/bin/python
'''Uploads a video to YouTube.'''

# Nono Martínez Alonso
# youtube.com/@NonoMartinezAlonso
# https://github.com/youtube/api-samples/blob/master/python/upload_video.py

import argparse
from http import client
import json
import os
from sys import stderr
import httplib2
import random
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

service: Resource = None
credentials: Credentials = None

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, client.NotConnected,
                        client.IncompleteRead, client.ImproperConnectionState,
                        client.CannotSendRequest, client.CannotSendHeader,
                        client.ResponseNotReady, client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secret.json"
AUTH_FILE = "auth.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def load_credentials() -> Credentials:
    global credentials

    if os.path.isfile(AUTH_FILE):
        try:
            creds = Credentials.from_authorized_user_file(AUTH_FILE, SCOPES)
            refresh_credentials(creds)
            credentials = creds

            print("Loaded credentials")
            return creds
        except Exception as e:
            print(e, file=stderr)

            return None


def save_credentials(creds: Credentials):
    with open(AUTH_FILE, "w") as file:
        json.dump(json.loads(creds.to_json()), file)
        print("Saved credentials")

    global credentials
    credentials = creds


def refresh_credentials(credentials: Credentials):
    if not credentials.valid:
        credentials.refresh(Request())
        build_service(credentials)
        save_credentials(credentials)
        print("Access token refreshed")


def build_service(credentials: Credentials):
    global service
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials, static_discovery=False)


# Authorize the request and store authorization credentials.
def get_authenticated_service() -> bool:
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES
    )

    credentials = flow.run_local_server(
        host="localhost",
        port=8088,
        success_message="Se ha iniciado sesión correctamente, Puede cerrar esta ventana.",
        open_browser=True
    )

    print("Got credentials from user")
    build_service(credentials)
    save_credentials(credentials)


def upload_video(title: str, description: str, filepath: str, tags: str) -> bool:
    global credentials, service

    refresh_credentials(credentials)
    tags = tags.split(',')

    body = dict(
        snippet=dict(
            title=f"{title} #shorts",
            description=f"{description} #shorts",
            tags=tags,
            categoryId="22"
        ),
        status=dict(
            privacyStatus="public"
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = service.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(filepath, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

    

# This method implements an exponential backoff strategy to resume a
# failed upload.


def resumable_upload(request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print('Video id "%s" was successfully uploaded.' %
                          response['id'])
                else:
                    exit('The upload failed with an unexpected response: %s' % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = 'A retriable error occurred: %s' % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print('Sleeping %f seconds and then retrying...' % sleep_seconds)
            time.sleep(sleep_seconds)