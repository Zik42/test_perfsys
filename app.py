# TODO inst, formatter
import os
import boto3
import json
import requests

import time
import aiohttp
import asyncio
from functools import reduce

client_stepfunctions = boto3.client('stepfunctions')
client_dynamodb = boto3.client('dynamodb')

WEBSITES_TABLE = os.environ['WEBSITES_TABLE']

BAD_REQUEST_RESPONSE = {
    "statusCode": 400,
}

SERVER_ERROR_RESPONSE = {
    "statusCode": 500,
}

loop = asyncio.get_event_loop()


def save_website_load_time(url, load_time):
    client_dynamodb.put_item(
        TableName=WEBSITES_TABLE,
        Item={
            'website': {'S': url },
            'load_time': {'S': load_time }
        }
    )


def get_website_with_load_time(url):
    time_start = time.time()

    try:
        response = requests.get(url)
    except:
        pass

    load_time = time.time() - time_start
    return response, load_time


def process_next_step_urls(reponseText):
    """ Return dict of next steps, rss or instagram """
    return {"rss": None, "instagram": None}




def process_website_url(event, _):

    url = event

    response, load_time = get_website_with_load_time(url)
    save_website_load_time(load_time)

    next_steps = process_next_step(response.text)

    return next_steps


def validate_urls(urls):
    if not isinstance(urls, list):
        raise TypeError
    return urls


def create_job(event, context):
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']

    #WEBSITES_STATE_MACHINE_ARN = "arn:aws:states:us-east-1:938668680897:stateMachine:ProcessWebsiteStateMachine-eH3mLiJJjeyc"

    try:
        body_json = json.loads(event.get('body'))
        urls = body_json['websites']
        validate_urls(urls)
    except KeyError, TypeError:
        return BAD_REQUEST_RESPONSE
    except Exception as e:
        print(e)
        return SERVER_ERROR_RESPONSE

    for url in urls:
        try:
            client_stepfunctions.start_execution(
                stateMachineArn=WEBSITES_STATE_MACHINE_ARN, input=json.dumps(url))

        except (client_stepfunctions.exceptions.InvalidArn,
                client_stepfunctions.exceptions.StateMachineDoesNotExist):
            return BAD_REQUEST_RESPONSE

        except (client_stepfunctions.exceptions.ExecutionLimitExceeded,
                client_stepfunctions.exceptions.ExecutionAlreadyExists,
                client_stepfunctions.exceptions.InvalidExecutionInput,
                client_stepfunctions.exceptions.InvalidName,
                client_stepfunctions.exceptions.StateMachineDeleting):
            return SERVER_ERROR_RESPONSE

    return {
        'statusCode': 200,
    }


def get_jobs(event, context):
    """ Returns list of jobs """
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']

    try:
        response = client_stepfunctions.list_executions(
            stateMachineArn=WEBSITES_STATE_MACHINE_ARN,
            maxResults=100,
        )
    except (client_stepfunctions.exceptions.InvalidArn,
            client_stepfunctions.exceptions.InvalidToken,
            client_stepfunctions.exceptions.StateMachineDoesNotExist):
        return BAD_REQUEST_RESPONSE

    try:
        result = []
        for execution in response['executions']:
            result.append({
                'executionArn': execution['executionArn'],
                'status': execution['status'],
            })
    except KeyError:
        return SERVER_ERROR_RESPONSE

    return {'statusCode': 200, 'body': json.dumps(result)}


def get_job(event, context):
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']
    try:
        job_id = event['pathParameters']['id']
    except KeyError:
        return BAD_REQUEST_RESPONSE

    try:
        response = client_stepfunctions.describe_execution(
            executionArn=job_id, )
    except (client_stepfunctions.exceptions.InvalidArn,
            client_stepfunctions.exceptions.ExecutionDoesNotExist):
        return BAD_REQUEST_RESPONSE

    try:
        job = {
            'executionArn': response['executionArn'],
            'status': response['status']
        }
    except KeyError:
        return SERVER_ERROR_RESPONSE

    return {'statusCode': 200, 'body': json.dumps(job)}


def get_websites(event, context):

    response = client_dynamodb.query(
        TableName=WEBSITES_TABLE,
        Limit=100
    )
    print(response)

    return json.dups({
        response
    })



def get_website(event, context):
    resp = client_dynamodb.get_item(
        TableName=USERS_TABLE,
        Key={
            'userId': { 'S': user_id }
        }
    )

    return json.dumps({ })
