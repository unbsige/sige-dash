from datetime import datetime

from config import BASE_URL, PASSWORD_UED, USERNAME_UED

from app.collectors.csisolar_auth import CSISolarOAuthClient
from app.collectors.csisolar_client import CSISolarClient

oauth_client = CSISolarOAuthClient()
response_data = oauth_client.login(USERNAME_UED, PASSWORD_UED)

access_token = response_data.get("access_token")
access_token_class = oauth_client.access_token
if access_token != access_token_class:
    print("✗ Tokens de acesso não correspondem")

print("\nResposta do login:")
if response_data:
    print(f"  - Acesso: {response_data.get('access_token')[:7]}*******")
    print(f"  - Expira em: {response_data.get('expires_in')} segundos")
    print(f"  - Escopo: {response_data.get('scope')}")
    print(f"  - MDC: {response_data.get('mdc')}")
    print(f"  - JTI: {response_data.get('jti')}")


client_csi = CSISolarClient(token=oauth_client.access_token, base_url=BASE_URL)

status = client_csi.get_rate_limit_status()
print("Status inicial:")
print(status)


start_date = datetime(2022, 1, 1)
end_date = datetime(2025, 9, 1)
response_data = client_csi.get_power_range(
    DEVICE_ID, start_date, end_date, granularity="daily"
)
