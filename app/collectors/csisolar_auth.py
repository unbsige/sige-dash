import hashlib
import json

import brotli
import httpx
from config.settings import INVERTERS


class CSISolarOAuthClient:
    def __init__(self, base_url=None, debug=False):
        self.base_url = base_url or "https://webmonitoring-gl.csisolar.com"
        self.access_token = None
        self.refresh_token = None
        self.debug = debug

        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
        }

        self.client = httpx.Client(
            headers=self.default_headers,
            follow_redirects=True,
            timeout=30.0,
        )

    def login(self, username, password):
        login_page_url = f"{self.base_url}/home/login"
        try:
            login_page_response = self.client.get(login_page_url)
            login_page_response.raise_for_status()
            print(f"✓ Página de login acessada: {login_page_response.status_code}")
        except httpx.RequestError as e:
            print(f"✗ Erro ao acessar página de login: {e}")
            return False

        login_headers = {
            **self.default_headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/home/login",
        }

        oauth_url = f"{self.base_url}/home/oauth-s/oauth/token"
        print(f"Tentando login para usuário: {username}")
        print(f"Endpoint: {oauth_url}")

        try:
            return self._execute_login_request(oauth_url, login_headers)
        except httpx.RequestError as e:
            print(f"✗ Erro na requisição de login: {e}")
            return False

    def _execute_login_request(self, oauth_url, login_headers):
        response = self.client.post(oauth_url, headers=login_headers)
        print(f"Status da requisição: {response.status_code}")

        if response.status_code == 200:
            return self._process_login_response(response)
        print(f"✗ Falha no login: {response.status_code}")
        self._debug_response(response)
        return False

    def _process_login_response(self, response: httpx.Response):
        if self.debug:
            self._debug_login_response(response)

        json_data = self._safe_json_decode(response)
        if json_data is None:
            print("✗ Não foi possível decodificar a resposta JSON")
            return False

        return self._extract_and_store_tokens(json_data)

    def _safe_json_decode(self, response: httpx.Response):
        try:
            return response.json()
        except Exception as e:
            print(f"response.json() falhou: {type(e).__name__}: {e}")

            content_encoding = response.headers.get("content-encoding")
            if content_encoding == "br":
                try:
                    print("Decodificando conteúdo com Brotli...")
                    decompressed = brotli.decompress(response.content)
                    text_content = decompressed.decode("utf-8")
                    return json.loads(text_content)
                except Exception as decode_error:
                    print(f"✗ Erro na decodificação Brotli: {decode_error}")

            try:
                text_content = response.text
                return json.loads(text_content)
            except Exception as fallback_error:
                print(f"✗ Erro na decodificação fallback: {fallback_error}")

            return None

    def _extract_and_store_tokens(self, json_data):
        if json_data is None:
            print("✗ Não foi possível decodificar a resposta JSON")
            return False

        self.access_token = json_data.get("access_token")
        self.refresh_token = json_data.get("refresh_token")

        if not self.access_token:
            print("✗ Token de acesso não encontrado na resposta")
            print(f"  Dados recebidos: {json_data}")
            return False

        self.client.headers["Authorization"] = f"Bearer {self.access_token}"
        print("✓ Login realizado com sucesso!")
        return json_data

    def _get_password_hash(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _debug_response(self, response: httpx.Response) -> None:
        print("\nDEBUG da Resposta:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        print(f"  Encoding: {response.encoding}")
        print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"  Content-Length: {len(response.content)} bytes")

    def refresh_access_token(self):
        if not self.refresh_token:
            print("✗ Refresh token não disponível")
            return False

        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        oauth_url = f"{self.base_url}/home/oauth-s/oauth/token"

        try:
            response = self.client.post(oauth_url, data=refresh_data)

            if response.status_code == 200:
                token_data = self._safe_json_decode(response)
                if token_data:
                    self.access_token = token_data.get("access_token")

                    self.client.headers["Authorization"] = f"Bearer {self.access_token}"

                    print("✓ Token renovado com sucesso!")
                    return True

            print(f"✗ Falha ao renovar token: {response.status_code}")
            return False

        except httpx.RequestError as e:
            print(f"✗ Erro ao renovar token: {e}")
            return False

    def close(self):
        self.client.close()

    def __enter__(self):
        return self
