#!/usr/bin/env python3

'''Simple Json Adapter HackAIR

Usage:
    service_callback.py --location=<location>
                        [--port=<port>]
                        [--host=<host>]
    service_callback.py (-h | --help)

Options:
    -h --help           Показвает это сообщение

    --port <port>
        Номер порта, на котором будет работать http сервер.
        [default: 8888]

    --host <host>
        Адрес на который будет слушать служба.

    --location <location>
        Квадрат, в котором производить поиск измерений
        Формат: "долгота,широта|долгота,широта"
        (Левая нижнаяя точка | Правая верхняя точка)
'''

import sys
import logging
import traceback
from operator import itemgetter

import aiohttp.web
from docopt import docopt

from lib.hackair_async import HackAIR

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Service:

    def __init__(self, port: int, location: str, host: str = '0.0.0.0'):
        self.port = port
        self.location = location
        self.host = host

        self.app = aiohttp.web.Application()

        self.app["hackair"] = HackAIR(location)

        # Route setup
        self.app.router.add_route('*', '/', self.handle_health)
        self.app.router.add_route('POST', '/search', self.handle_search)
        self.app.router.add_route('POST', '/query', self.handle_query)

    def start(self):
        aiohttp.web.run_app(self.app, port=self.port, host=self.host)

    async def handle_health(self, request):
        '''Проверить здоровье службы '''
        return aiohttp.web.HTTPOk()

    async def handle_search(self, request):
        '''/search'''
        # payload = await request.json()
        # target = payload.get("target", "")

        search = [
            "sensors",  # list sensors id
            "sensors_count",
            "pollutant_pm25",  #
            "pollutant_pm10",
        ]

        return aiohttp.web.json_response(search)

    async def handle_query(self, request):
        ''''''
        result = []

        payload = await request.json()

        date_from = payload["range"]["from"]
        date_to = payload["range"]["to"]

        for item in payload["targets"]:
            target = item["target"]
            ref_id = item["refId"]
            t = item["type"]

            if target == "sensors":
                result.append(
                    await self._target_sensors(request, date_from, date_to)
                )

            if target == "sensors_count":
                result.append(
                    await self._target_sensors_count(
                        request, date_from, date_to)
                )

            if target == "pollutant_pm25":
                result.append(
                    await self._target_pollutant_pm25(
                        request, date_from, date_to)
                )

            if target == "pollutant_pm10":
                result.append(
                    await self._target_pollutant_pm10(
                        request, date_from, date_to)
                )

        return aiohttp.web.json_response(result)

    async def _target_sensors(self, request, date_from, date_to) -> dict:
        # table
        r = {
            "columns": [
                {
                    "text": "sensor_id",
                },
            ],
            "rows": [],
            "type": "table"
        }
        res = await request.app['hackair'].get_sensors(date_from, date_to)

        for v in res:
            r["rows"].append([v])

        return r

    async def _target_sensors_count(self, request, date_from, date_to) -> dict:
        # table
        r = {
            "columns": [
                {
                    "text": "sensor_count",
                },
            ],
            "rows": [],
            "type": "table"
        }

        c = len(await request.app['hackair'].get_sensors(date_from, date_to))
        r["rows"].append([c])

        return r

    async def _target_pollutant_pm25(self, request, date_from, date_to) -> dict:
        # timeseries
        r = {
            "target": "pollutant_pm25",
            "datapoints": []
        }
        t = await request.app['hackair'].get_pollutant_pm25(date_from, date_to)
        r["datapoints"] = t

        return r

    async def _target_pollutant_pm10(self, request, date_from, date_to) -> dict:
        # timeseries
        r = {
            "target": "pollutant_pm10",
            "datapoints": []
        }
        t = await request.app['hackair'].get_pollutant_pm10(date_from, date_to)
        r["datapoints"] = t

        return r


if __name__ == "__main__":
    arguments = docopt(__doc__)

    location = arguments["--location"]
    host = arguments["--host"]

    # Http
    try:
        port = int(arguments['--port'])
    except ValueError:
        print("Порт должен быть числом")
        sys.exit(-1)

    # Запуск службы
    srv = Service(port=port, location=location, host=host)

    try:
        srv.start()
    except Exception as e:
        print("Произошла критическая ошибка:")
        tr = traceback.format_exc()
        print(tr)
        sys.exit(-1)
