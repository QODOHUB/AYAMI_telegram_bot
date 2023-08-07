import datetime
import logging
from uuid import UUID

import aiohttp

from tgbot.services.iiko.schemas import *


class Iiko:
    def __init__(self, api_login, retries_count: int = 3):
        self.api_login = api_login
        self.last_token_update = None
        self.token = None
        self.retries_count = retries_count

        self.headers = {
            'Authorization': 'Bearer {token}',
            'Content-Type': 'application/json'
        }

    async def create_or_update_customer(self, customer: CreateOrUpdateCustomer):
        url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/create_or_update'
        payload = customer.model_dump()

        status, result = await self._post_request(url, payload)
        return result['id']

    async def get_customer_info(self, get_type: str, get_value: str, organization_id: UUID = None):
        url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/info'

        possible_types = ('id', 'phone', 'email', 'cardTrack', 'cardNumber')
        if get_type not in possible_types:
            raise ValueError(f'Get type must be from that list: {possible_types}')
        payload = {
            get_type: get_value,
            'type': get_type,
            'organizationId': organization_id
        }

        status, result = await self._post_request(url, payload)
        return Customer(**result)

    async def get_organizations(
            self,
            extended_info: bool,
            include_disabled: bool,
            external_data: list[str] = None,
            orgs_ids: list[str | UUID] = None
    ) -> OrganizationsResult:
        url = 'https://api-ru.iiko.services/api/1/organizations'
        payload = {
            'organizationIds': orgs_ids,
            'returnAdditionalInfo': extended_info,
            'includeDisabled': include_disabled,
            'returnExternalData': external_data
        }

        status, result = await self._post_request(url, payload)
        return OrganizationsResult(**result)

    async def update_token(self) -> bool:
        new_token = await self.get_new_token()
        if isinstance(new_token, Error):
            logging.error(str(new_token))
            return False

        self.token = new_token.token
        self.headers['Authorization'] = f'Bearer {new_token.token}'
        self.last_token_update = datetime.datetime.now()

        return True

    async def get_new_token(self) -> AccessTokenResult | Error:
        url = 'https://api-ru.iiko.services/api/1/access_token'
        payload = {
            'apiLogin': self.api_login
        }

        status, result = await self._request('POST', url, check_token=False, json=payload)
        return AccessTokenResult(**result)

    async def _get_request(self, url):
        return await self._request('GET', url)

    async def _post_request(self, url, payload):
        return await self._request('POST', url, json=payload)

    async def _request(self, method, url, check_token=True, retires=1, **kwargs):
        if method not in ('POST', 'GET', 'PUT', 'DELETE', 'PATCH'):
            raise ValueError(f'Unknown method "{method}"')

        if check_token and (not self.token or (datetime.datetime.now() - self.last_token_update < datetime.timedelta(minutes=55))):
            result = await self.update_token()
            if not result:
                raise ApiError('Error during updating token. See error in previous log')

        async with aiohttp.ClientSession(headers=self.headers) as session:
            match method:
                case 'POST':
                    request = session.post
                case 'GET':
                    request = session.get
                case 'PUT':
                    request = session.put
                case 'DELETE':
                    request = session.delete
                case 'PATCH':
                    request = session.patch

            async with request(url, **kwargs) as response:
                if not response.ok:
                    if response.status == 401:
                        await self.update_token()
                    if retires > self.retries_count:
                        raise ApiError(str(await response.text()))
                    await self._request(method, url, check_token, retires + 1, **kwargs)

                json_resp = await response.json()

        return response.status, json_resp
