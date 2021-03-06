# TODO inst, formatter
import os
import boto3
import json
import requests
import feedparser
from urllib.parse import urlparse
import time
from functools import reduce
from bs4 import BeautifulSoup as bs4

client_stepfunctions = boto3.client('stepfunctions')
client_dynamodb = boto3.client('dynamodb')

WEBSITES_TABLE = os.environ['WEBSITES_TABLE']
WEBSITES_STATE_MACHINE_ARN = os.environ.get('WEBSITES_STATE_MACHINE_ARN')

BAD_REQUEST_RESPONSE = {
    "statusCode": 400,
}

SERVER_ERROR_RESPONSE = {
    "statusCode": 500,
}


def findfeed(url, htmlText):
    result = []
    possible_feeds = []
    html = bs4(htmlText, 'html.parser')
    feed_urls = html.findAll('link', rel='alternate')
    if len(feed_urls) > 1:
        for f in feed_urls:
            t = f.get('type', None)
            if t:
                if 'rss' in t or 'xml' in t:
                    href = f.get('href', None)
                    if href:
                        possible_feeds.append(href)

    parsed_url = urlparse(url)
    base = parsed_url.scheme + '://' + parsed_url.hostname
    atags = html.findAll('a')
    for a in atags:
        href = a.get('href', None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base + href)

    for url in list(set(possible_feeds)):
        try:
            f = feedparser.parse(url)
            if len(f.entries) > 0:
                result = f['entries'][:5]
            return json.dumps(result)
        except Exception as e:
            print(e)


def save_website(domain, load_time, rss=None, instagram=None):
    item = {'domain': {'S': str(domain)}, 'load_time': {'S': str(load_time)}}

    if rss:
        item['rss'] = {'S': str(rss)}
    if instagram:
        item['instagram'] = {'S': str(instagram)}

    client_dynamodb.put_item(TableName=WEBSITES_TABLE, Item=item)
    return {
        "domain": domain,
        "load_time": load_time,
        "rss": rss,
        "instagram": instagram
    }


def get_website_with_load_time(url):
    time_start = time.time()
    response = requests.get(url)
    load_time = time.time() - time_start
    return response, load_time


def process_website(event, _):

    domain = event['domain']
    webhook = event['webhook']
    url = f"https://{domain}"

    response, load_time = get_website_with_load_time(url)

    rss = findfeed(url, response.text)
    # TODO
    instagram = None

    website_json = save_website(domain, load_time, rss, instagram)

    return website_json


def webhook(event, _):
    requests.post(event['webhook'], json=event)


def validate_domains(domains):
    if not isinstance(domains, list):
        raise TypeError
    return domains


def create_job(event, context):

    try:
        body_json = json.loads(event.get('body'))
        domains = body_json['domains']
        webhook = body_json['webhook']
        validate_domains(domains)
    except (KeyError, TypeError):
        return BAD_REQUEST_RESPONSE
    except Exception as e:
        print(e)
        return SERVER_ERROR_RESPONSE

    for domain in domains:
        try:
            client_stepfunctions.start_execution(
                stateMachineArn=WEBSITES_STATE_MACHINE_ARN,
                input=json.dumps({
                    "domain": domain,
                    "webhook": webhook
                }))

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
    try:
        job_arn = event['pathParameters']['arn']
    except KeyError:
        return BAD_REQUEST_RESPONSE

    try:
        response = client_stepfunctions.describe_execution(
            executionArn=job_arn, )
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


def db_website_item_to_json(item):
    res = {'load_time': item['load_time']['S'], 'domain': item['domain']['S']}

    try:
        res['rss'] = item['rss']['S']
    except KeyError:
        pass
    try:
        res['instagram'] = item['instagram']['S']
    except KeyError:
        pass

    return res


def get_websites(event, context):

    try:
        response = client_dynamodb.scan(TableName=WEBSITES_TABLE, Limit=100)
    except (client_dynamodb.exceptions.ProvisionedThroughputExceededException,
            client_dynamodb.exceptions.ResourceNotFoundException,
            client_dynamodb.exceptions.RequestLimitExceeded,
            client_dynamodb.exceptions.InternalServerError) as e:
        print(e)
        return SERVER_ERROR_RESPONSE

    print(response)
    result = []
    for item in response.get('Items', []):
        result.append(db_website_item_to_json(item))
    return {"statusCode": 200, "body": json.dumps(result)}


def get_website(event, context):
    try:
        domain = event['pathParameters']['domain']
    except KeyError as e:
        print(e)
        return BAD_REQUEST_RESPONSE

    try:
        r = client_dynamodb.get_item(TableName=WEBSITES_TABLE,
                                            Key={'domain': {
                                                'S': domain
                                            }})
    except (client_dynamodb.exceptions.ProvisionedThroughputExceededException,
            client_dynamodb.exceptions.ResourceNotFoundException,
            client_dynamodb.exceptions.RequestLimitExceeded,
            client_dynamodb.exceptions.InternalServerError) as e:
        print(e)
        return SERVER_ERROR_RESPONSE


    try:
        item = r['Item']
    except KeyError:
        return {"statusCode": 404}

    return {
        "statusCode": 200,
        "body": json.dumps(db_website_item_to_json(item))
    }
