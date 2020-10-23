from flask import Flask, request, jsonify

import time
import aiohttp
import asyncio
from functools import reduce


app = Flask(__name__)

DEFAULT_TIMEOUT_FOR_URL = 3


loop = asyncio.get_event_loop()

async def get_website_load_time(time_start, url):
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_FOR_URL)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout): pass
            load_time = time.time() - time_start
            url_status = f"{load_time}s"
        except aiohttp.client_exceptions.InvalidURL as e:
            url_status = "Invalid server url"
        except asyncio.TimeoutError as e:
            url_status = "Timeout"

    return  { url: url_status }

async def get_websites_load_time(urls):
    print(urls)
    time_start = time.time()
    tasks = [get_website_load_time(time_start, url) for url in urls]

    result = await asyncio.gather(*tasks)

    # Merge list of dicts into one.
    result = reduce(lambda acc, e: {**acc, **e}, result)
    return result

@app.route("/", methods=["POST"])
def root():
    try:
        urls = request.get_json()['urls']
    except KeyError as e:
        return "Bad request", 400
    result = loop.run_until_complete(get_websites_load_time(urls))
    return jsonify(result)
