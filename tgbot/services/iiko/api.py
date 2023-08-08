import datetime
import logging

import aiohttp

from tgbot.services.iiko import schemas


class Iiko:
    def __init__(self, api_login, default_organization_id, retries_count: int = 3):
        self.api_login = api_login
        self.last_token_update = None
        self.token = None
        self.retries_count = retries_count
        self.default_organization_id = default_organization_id

        self.headers = {
            'Authorization': 'Bearer {token}',
            'Content-Type': 'application/json'
        }

    async def get_terminal_groups(
            self,
            organization_ids: list[str],
            include_disabled=False,
            external_data: list[str]=None
    ) -> schemas.TerminalGroupsResult:
        url = 'https://api-ru.iiko.services/api/1/terminal_groups'
        payload = {
            'organizationIds': organization_ids,
            'includeDisabled': include_disabled,
            'returnExternalData': external_data
        }

        result = await self._post_request(url, payload)
        return schemas.TerminalGroupsResult(**result)

    async def get_menu(self, organization_id: str, start_revision: int = None) -> schemas.MenuResult:
        url = 'https://api-ru.iiko.services/api/1/nomenclature'
        payload = {
            'organizationId': organization_id,
            'startRevision': start_revision
        }

        result = await self._post_request(url, payload)
        return schemas.MenuResult(**result)

    async def create_or_update_customer(self, customer: schemas.CreateOrUpdateCustomer) -> str:
        if customer.organizationId is None:
            customer.organizationId = self.default_organization_id

        url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/create_or_update'
        payload = customer.model_dump()

        result = await self._post_request(url, payload)
        return result['id']

    async def get_customer_info(self, get_type: str, get_value: str, organization_id: str = None) -> schemas.Customer:
        if organization_id is None:
            organization_id = self.default_organization_id

        url = 'https://api-ru.iiko.services/api/1/loyalty/iiko/customer/info'

        possible_types = ('id', 'phone', 'email', 'cardTrack', 'cardNumber')
        if get_type not in possible_types:
            raise ValueError(f'Get type must be from that list: {possible_types}')
        payload = {
            get_type: get_value,
            'type': get_type,
            'organizationId': organization_id
        }

        result = await self._post_request(url, payload)
        return schemas.Customer(**result)

    async def get_organizations(
            self,
            extended_info: bool,
            include_disabled: bool,
            external_data: list[str] = None,
            orgs_ids: list[str] = None
    ) -> schemas.OrganizationsResult:
        url = 'https://api-ru.iiko.services/api/1/organizations'
        payload = {
            'organizationIds': orgs_ids,
            'returnAdditionalInfo': extended_info,
            'includeDisabled': include_disabled,
            'returnExternalData': external_data
        }

        result = await self._post_request(url, payload)
        return schemas.OrganizationsResult(**result)

    async def update_token(self) -> bool:
        new_token = await self.get_new_token()
        if isinstance(new_token, schemas.Error):
            logging.error(str(new_token))
            return False

        self.token = new_token.token
        self.headers['Authorization'] = f'Bearer {new_token.token}'
        self.last_token_update = datetime.datetime.now()

        return True

    async def get_new_token(self) -> schemas.AccessTokenResult | schemas.Error:
        url = 'https://api-ru.iiko.services/api/1/access_token'
        payload = {
            'apiLogin': self.api_login
        }

        result = await self._request('POST', url, check_token=False, json=payload)
        return schemas.AccessTokenResult(**result)

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
                raise schemas.ApiError('Error during updating token. See error in previous log')

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
                        raise schemas.ApiError(str(await response.text()))
                    await self._request(method, url, check_token, retires + 1, **kwargs)

                json_resp = await response.json()

        return json_resp
