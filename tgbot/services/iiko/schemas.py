import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiError(Exception):
    pass


class GuestCard(BaseModel):
    id: UUID
    track: str
    number: str
    validToDate: datetime.datetime | None


class GuestCategory(BaseModel):
    id: UUID
    name: str
    isActive: bool
    isDefaultForNewGuests: bool


class GuestWallet(BaseModel):
    id: UUID
    name: str
    type: int
    balance: float


class CreateOrUpdateCustomer(BaseModel):
    id: UUID = None
    referrerId: UUID = None
    name: str = None
    surname: str = None
    middleName: str = None
    phone: str = None
    birthday: datetime.date = None
    email: str | None
    sex: int = 0  # 0 - not specified, 1 - male, 2 - female
    consentStatus: int = 0  # 0 - unknown, 1 - given, 2 - revoked
    shouldReceivePromoActionsInfo: bool = None
    userData: str = None
    organizationId: UUID



class Customer(BaseModel):
    id: UUID
    referrerId: UUID | None
    name: str | None
    surname: str | None
    middleName: str | None
    comment: str | None
    phone: str | None
    cultureName: str | None
    birthday: datetime.date | None
    email: str | None
    sex: int  # 0 - not specified, 1 - male, 2 - female
    consentStatus: int  # 0 - unknown, 1 - given, 2 - revoked
    anonymized: bool
    cards: list[GuestCard]
    categories: list[GuestCategory]
    walletBalances: list[GuestWallet]
    userData: str | None
    shouldReceivePromoActionsInfo: bool | None
    shouldReceiveLoyaltyInfo: bool | None
    shouldReceiveOrderStatusInfo: bool | None
    personalDataConsentFrom: datetime.datetime | None
    personalDataConsentTo: datetime.datetime | None
    personalDataProcessingFrom: datetime.datetime | None
    personalDataProcessingTo: datetime.datetime | None
    isDeleted: bool | None


class ExternalData(BaseModel):
    key: str
    value: str


class Organization(BaseModel):
    responseType: str  # 'simple' or 'extended'
    id: UUID
    name: str | None
    code: str | None
    externalData: list[ExternalData] | None


class ExtendedOrganization(BaseModel):
    country: str | None
    restaurantAddress: str | None
    latitude: float
    longitude: float
    useUaeAddressingSystem: bool
    version: str
    currencyIsoName: str | None
    currencyMinimumDenomination: float | None
    countryPhoneCode: str | None
    marketingSourceRequiredInDelivery: bool | None
    defaultDeliveryCityId: UUID | None
    deliveryCityIds: list[UUID] | None
    deliveryServiceType: str | None  # "CourierOnly" "SelfServiceOnly" "CourierAndSelfService"
    defaultCallCenterPaymentTypeId: UUID | None
    orderItemCommentEnabled: bool | None
    inn: str | None
    addressFormatType: str  # "Legacy" "City" "International" "IntNoPostcode"
    isConfirmationEnabled: bool | None
    confirmAllowedIntervalInMinutes: int | None
    isCloud: bool
    isAnonymousGuestsAllowed: bool
    addressLookup: list[str]  # Items Enum: "DaData" "GetAddress"


class OrganizationsResult(BaseModel):
    correlationId: UUID
    organizations: list[Organization | ExtendedOrganization]


class AccessTokenResult(BaseModel):
    correlationId: UUID
    token: str


class Error(BaseModel):
    correlationId: UUID
    errorDescription: str
    error: str | None
