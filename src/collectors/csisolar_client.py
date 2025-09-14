import logging
import random
import time
from datetime import datetime

import httpx
import pandas as pd
from dateutil.relativedelta import relativedelta


class CSISolarClient:
    def __init__(self, token, base_url, headers=None):
        self.token = token
        self.base_url = base_url
        self.remaining_tokens = 20
        self.burst_capacity = 20
        self.replenish_rate = 8
        self.last_request_time = None

        self.headers = headers or self.get_headers()
        self.headers["Authorization"] = f"Bearer {self.token}"
        self.client = httpx.Client(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
        )

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_headers(self):
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt-BR,pt;q=0.5",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "webmonitoring-gl.csisolar.com",
            "Pragma": "no-cache",
            "Referer": "https://webmonitoring-gl.csisolar.com/home/plant/infos/data",
            "Sec-CH-UA": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        }

    def update_rate_limit_from_headers(self, headers):
        try:
            self.remaining_tokens = int(headers.get("X-RateLimit-Remaining", self.remaining_tokens))
            self.burst_capacity = int(headers.get("X-RateLimit-Burst-Capacity", self.burst_capacity))
            self.replenish_rate = int(headers.get("X-RateLimit-Replenish-Rate", self.replenish_rate))
            self.logger.info(f"Rate limit atualizado: {self.remaining_tokens}/{self.burst_capacity}")
        except (ValueError, TypeError):
            self.logger.warning("Erro ao parsear headers de rate limit")

    def calculate_wait_time(self):
        mini_delay = random.uniform(0.005, 0.03)  # 5 a 30ms aleatório

        if self.remaining_tokens >= 1:
            return mini_delay

        wait_time = 1 / self.replenish_rate
        return wait_time + mini_delay

    def wait_if_needed(self):
        wait_time = self.calculate_wait_time()
        self.logger.info(f"Aguardando {wait_time:.2f}s devido ao rate limit...")
        time.sleep(wait_time)

    def make_request(self, method, endpoint, **kwargs):
        self.wait_if_needed()
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.client.request(method, url, **kwargs)
            self.update_rate_limit_from_headers(response.headers)
            self.last_request_time = time.time()

            if response.status_code == 429:
                self.logger.warning("Rate limit excedido! Headers podem estar desatualizados.")
                time.sleep(2)
                return self.make_request(method, endpoint, **kwargs)

            response.raise_for_status()
            return response

        except httpx.RequestError as e:
            self.logger.exception(f"Erro na requisição: {e}")
            raise

    def get_power_data_daily(self, device_id, date):
        endpoint = f"/home/maintain-s/history/power/{device_id}/record"
        params = {
            "year": date.year,
            "month": date.month,
            "day": date.day,
        }

        response = self.make_request("GET", endpoint, params=params)
        return response.json()

    def get_power_data_month(self, device_id, date):
        endpoint = f"/home/maintain-s/history/power/{device_id}/stats/month"
        params = {
            "year": date.year,
            "month": date.month,
        }

        response = self.make_request("GET", endpoint, params=params)
        return response.json()

    def get_power_data_year(self, device_id, date):
        endpoint = f"/home/maintain-s/history/power/{device_id}/stats/year"
        params = {"year": date.year}

        response = self.make_request("GET", endpoint, params=params)
        return response.json()

    def get_power_data_total(self, device_id):
        endpoint = f"/home/maintain-s/history/power/{device_id}/stats/total"
        response = self.make_request("GET", endpoint)
        return response.json()

    def get_power_range(self, device_id, start_date, end_date, granularity="daily"):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if granularity not in ["daily", "monthly"]:
            raise ValueError("Granularity must be 'daily' or 'monthly'")

        function = self.get_power_data_month if granularity == "monthly" else self.get_power_data_daily

        current_date = start_date
        results = []
        request_count = 0

        self.logger.info(f"Coletando dados de {current_date} até {end_date}")
        self.logger.info(f"Taxa sustentável: {self.replenish_rate} req/s")

        while current_date <= end_date:
            self.wait_if_needed()

            try:
                data = function(device_id, current_date)
                results.append({"date": current_date.strftime("%Y-%m-%d"), "data": data})
                request_count += 1
                if request_count % 10 == 0:
                    eta = (self.burst_capacity - self.remaining_tokens) / self.replenish_rate
                    tokens = f"{self.remaining_tokens}/{self.burst_capacity}"
                    self.logger.info(f"Progress: {request_count} requests | Tokens: {tokens} | ETA: {eta:.1f}s")

            except Exception as e:
                self.logger.exception(f"Erro ao obter dados para {current_date}: {e}")

            if granularity == "monthly":
                current_date = current_date.replace(day=1) + relativedelta(months=1)
            else:
                current_date += pd.Timedelta(days=1)

        self.logger.info(f"Coleta concluída! {len(results)} dias processados.")
        return results

    def get_rate_limit_status(self):
        return {
            "remaining_tokens": self.remaining_tokens,
            "burst_capacity": self.burst_capacity,
            "replenish_rate": self.replenish_rate,
            "estimated_wait_for_full": (self.burst_capacity - self.remaining_tokens) / self.replenish_rate,
            "sustainable_rate_per_hour": self.replenish_rate * 3600,
        }
