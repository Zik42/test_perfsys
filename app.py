# TODO inst, formatter
import os
import boto3
import json
import requests

import time
import aiohttp
import asyncio
from functools import reduce


client_stepfunctions= boto3.client('stepfunctions')

from client.exceptions import *

BAD_REQUEST_RESPONSE = {
    "statusCode": 400,
}

SERVER_ERROR_RESPONSE = {
    "statusCode": 500,
}

loop = asyncio.get_event_loop()

def save_website_load_time(url, load_time):
    pass

def get_website_with_load_time(url):
    time_start = time.time()

    try:
        response = requests.get(url)
    except:
        pass

    load_time = time.time() - time_start
    return  response, load_time

def process_next_step_urls(reponseText):
    """ Return dict of next steps, rss or instagram """
    pass


def validate_urls(urls):
    # I need some lib for schema...
    if not isinstance(urls, list):
        raise TypeError
    return urls

def process_website(event, context):
    print(event)
    print(context)

    response, load_time = get_website_with_load_time(url)
    save_website_load_time(load_time)

    next_steps = process_next_step(response.text)

    return next_steps



def create_job(event, context):
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']

    try:
        body_json = json.loads(event.get('body'))
    except Exception as e:
        print(e)

    try:
        client_stepfunctions.start_execution(
            stateMachineArn=WEBSITES_STATE_MACHINE_ARN,
            input=json.dumps(urls)
        )
    except (
                client_stepfunctions.exceptions.StateMachineDoesNotExist
        client_stepfunctions.exceptions.InvalidArn,
        ):
        return BAD_REQUEST_RESPONSE

    except (
        client_stepfunctions.exceptions.ExecutionLimitExceeded,
        client_stepfunctions.exceptions.ExecutionAlreadyExists
        client_stepfunctions.exceptions.InvalidExecutionInput
        client_stepfunctions.exceptions.InvalidName
        client_stepfunctions.exceptions.StateMachineDeleting
    ):
    return {
        'statusCode': 200,
    }


def get_jobs(event, context):
    """ Returns list of jobs """
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']

    response = client.list_executions(
        stateMachineArn=WEBSITES_STATE_MACHINE_ARN,
        maxResults=100,
    )

    try:
        result = []
        for execution in response['executions']:
            result.append({
                    'executionArn': execution['executionArn'],
                    'status': execution['status'],
                })
    except KeyError:
        return SERVER_ERROR_RESPONSE

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


def get_job(event, context):
    WEBSITES_STATE_MACHINE_ARN = os.environ['WEBSITES_STATE_MACHINE_ARN']
    try:
        job_id = event['pathParameters']['id']
        print(job_id)
    except KeyError:
        return BAD_REQUEST_RESPONSE

    try:
        response = client.describe_execution(
            executionArn=job_id,
        )
    except (client.exceptions.InvalidArn, client.exceptions.ExecutionDoesNotExist):
        return BAD_REQUEST_RESPONSE


    try:
        job = {
            'executionArn': response['executionArn'],
            'status': response['status']
        }
    except KeyError:
        return SERVER_ERROR_RESPONSE

    return {
        'statusCode': 200,
        'body': json.dumps(job)
    }

def get_websites(event, context):
    print(event)
    print(response)

def get_website(event, context):
    print(event)
    print(response)
