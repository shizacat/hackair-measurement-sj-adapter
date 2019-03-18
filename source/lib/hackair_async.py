from datetime import datetime, timedelta
from operator import itemgetter

import aiohttp


class HackAIR:

    url = "https://api.hackair.eu"
    path_measurements = "/measurements"

    def __init__(self, location: str):
        self.location = location

        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        )

    async def close(self):
        await self.session.close()

    async def get_sensors(self, date_from: str, date_to: str = None) -> list:
        r = await self._request(date_from, date_to)

        payload = await r.json()

        if payload.get("status_code", 200) != 200:
            print("Error", payload.get("message"))
            return []

        result = set()

        for item in payload.get("data", []):
            result.add(item["source_info"]["sensor"]["id"])

        return list(result)

    async def get_pollutant_pm25(self, date_from, date_to: str = None):
        r = await self._request(date_from, date_to)

        payload = await r.json()

        if payload.get("status_code", 200) != 200:
            print("Error", payload.get("message"))
            return []

        result = []

        for item in payload.get("data", []):
            if item["pollutant_q"]["name"] == "PM2.5_AirPollutantValue":
                result.append(
                    [
                        float(item["pollutant_q"]["value"]),
                        self.to_epoch(item["date_str"])
                    ]
                )

        result = sorted(result, key=itemgetter(1))

        return result

    async def get_pollutant_pm10(self, date_from, date_to: str = None):
        r = await self._request(date_from, date_to)

        payload = await r.json()

        if payload.get("status_code", 200) != 200:
            print("Error", payload.get("message"))
            return []

        result = []

        for item in payload.get("data", []):
            if item["pollutant_q"]["name"] == "PM10_AirPollutantValue":
                result.append(
                    [
                        float(item["pollutant_q"]["value"]),
                        self.to_epoch(item["date_str"])
                    ]
                )

        result = sorted(result, key=itemgetter(1))

        return result

    def to_epoch(self, dt_format):
        epoch = int((datetime.strptime(dt_format, "%Y-%m-%dT%H:%M:%SZ") - datetime(1970, 1, 1)).total_seconds()) * 1000
        return epoch
        # epoch = int(datetime.strptime(
        #     dt_format, "%Y-%m-%dT%H:%M:%SZ").timestamp()) * 1000
        # return epoch

    async def _request(self, date_from, date_to):
        r = await self.session.get(
            self.url + self.path_measurements,
            headers=self._get_header(),
            params=self._get_params(
                date_from,
                timestampEnd=date_to
            ),
            data=b""
        )
        return r

    def _get_header(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.hackair.v1+json"
        }
        return h

    def _get_params(
            self,
            timestampStart: str,
            timestampEnd: str = None,
            sensor: str = None):
        p = {
            "timestampStart": timestampStart,
            "location": self.location,
            "show": "all",
        }

        if timestampEnd is not None:
            p["timestampEnd"] = timestampEnd
        if sensor is not None:
            p["sensor"] = sensor

        return p
