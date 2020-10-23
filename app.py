from flask import Flask, request

import time
import aiohttp
import asyncio


app = Flask(__name__)

DEFAULT_TIMEOUT_FOR_URL = 3


loop = asyncio.get_event_loop()

async def get_website_load_time(time_start, url):
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_FOR_URL)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout): pass
        except aiohttp.client_exceptions.InvalidURL as e:
            return "Invalid server url"
        except asyncio.TimeoutError as e:
            return "Timeout"

    load_time = time.time() - time_start
    return  load_time

async def get_websites_load_time(urls):
    print(urls)
    time_start = time.time()
    tasks = [get_website_load_time(time_start, url) for url in urls]

    result = await asyncio.gather(*tasks)

    print(result)

    return "Meow."

@app.route("/", methods=["POST"])
def root():
    try:
        urls = request.get_json()['urls']
    except KeyError as e:
        return "Bad request", 400
    result = loop.run_until_complete(get_websites_load_time(urls))
    print(result)
    return "ok"
