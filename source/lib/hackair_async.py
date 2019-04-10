import asyncio
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

        self.interval_request = timedelta(hours=1)

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

    # async def get_pollutant_pm25(self, date_from, date_to: str = None):
    #     r = await self._request(date_from, date_to)

    #     payload = await r.json()

    #     if payload.get("status_code", 200) != 200:
    #         print("Error", payload.get("message"))
    #         return []

    #     result = []

    #     for item in payload.get("data", []):
    #         if item["pollutant_q"]["name"] == "PM2.5_AirPollutantValue":
    #             result.append(
    #                 [
    #                     float(item["pollutant_q"]["value"]),
    #                     self.to_epoch(item["date_str"])
    #                 ]
    #             )

    #     result = sorted(result, key=itemgetter(1))

    #     return result

    async def fetch_pollutant(self, ind: int, name_p: str, dt_from, dt_to):
        """Делает запрос

        Args:
            name_p - название показателя (PM2.5_AirPollutantValue)

        Return Список вида [ind, [[dt, value], ...]]
        """
        result = [ind, []]

        r = await self._request(dt_from, dt_to)
        payload = await r.json()

        if payload.get("status_code", 200) != 200:
            print("Error", payload.get("message"))
            return result

        for item in payload.get("data", []):
            if item["pollutant_q"]["name"] == name_p:
                result[1].append(
                    [
                        float(item["pollutant_q"]["value"]),
                        self.to_epoch(item["date_str"])
                    ]
                )

        result[1] = sorted(result[1], key=itemgetter(1))

        return result

    async def get_pollutant_pm25(self, date_from: str, date_to: str = None):
        """Разбивает интервал по часам и делает отдельный запрос
        для кождого т.к. максимально возвращается 600 точек

        Args:
            date_from - дата и время начала интервала,
                формат: 2016-10-31T06:33:44.866Z (в UTC)
            date_to - дата и время окончания интервала
                формат тот же

        Return:
        """
        result = []

        dt_from = self._to_date(date_from)
        dt_to = self._to_date(date_to)

        dt_range = self._get_range_date(dt_from, dt_to)
        for i in range(dt_range):
            task = asyncio.ensure_future(
                self.fetch_pollutant(
                    i, "PM2.5_AirPollutantValue", *dt_range[i]
                )
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        for r in sorted(responses, key=itemgetter(0)):
            result.extend(r[1])

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

    def _to_date(self, dt: str) -> datetime:
        """Format: 2016-10-31T06:33:44.866Z"""
        dt_filter = dt.replace("Z", "+0000")
        result = datetime.strptime(dt_filter, "%Y-%m-%dT%H:%M:%S.%f%z")
        result = result.replace(microsecond=0)
        return result

    def _get_range_date(self, dt_start, dt_end) -> list:
        """Разбивает отрезок на части

        Return  список пар дата_начало, дата_конец
        """
        result = []

        cstep = int((dt_end - dt_start) / self.interval_request)
        if cstep > 100:
            raise ValueError("Слишком большой интервал")

        is_first = 0
        step = 1
        d_last = dt_start
        while True:
            d = d_last + self.interval_request
            if d >= dt_end:
                d = dt_end

            v = (d_last + timedelta(seconds=1) * is_first, d)
            result.append(v)

            if d >= dt_end:
                return result

            is_first = 1
            d_last = d
