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
    id: str = None
    referrerId: UUID = None
    name: str = None
    surname: str = None
    middleName: str = None
    phone: str = None
    birthday: datetime.date = None
    email: str = None
    sex: int = 0  # 0 - not specified, 1 - male, 2 - female
    consentStatus: int = 0  # 0 - unknown, 1 - given, 2 - revoked
    shouldReceivePromoActionsInfo: bool = None
    userData: str = None
    organizationId: str


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
    externalData: list[ExternalData] | None = None


class ExtendedOrganization(Organization):
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


class TerminalGroupItem(BaseModel):
    id: UUID
    organizationId: UUID
    name: str
    timeZone: str
    externalData: list[ExternalData] | None = None


class TerminalGroup(BaseModel):
    organizationId: UUID
    items: list[TerminalGroupItem]


class TerminalGroupsResult(BaseModel):
    correlationId: UUID
    terminalGroups: list[TerminalGroup]
    terminalGroupsInSleep: list[TerminalGroup]


class OrganizationsResult(BaseModel):
    correlationId: UUID
    organizations: list[ExtendedOrganization | Organization]


class ProductGroup(BaseModel):
    imageLinks: list[str]
    parentGroup: UUID | None
    order: int
    isIncludedInMenu: bool
    isGroupModifier: bool
    id: UUID
    code: str | None
    name: str
    description: str | None
    additionalInfo: str | None
    tags: list[str] | None
    isDeleted: bool
    seoDescription: str | None
    seoText: str | None
    seoKeywords: str | None
    seoTitle: str | None


class ProductCategory(BaseModel):
    id: UUID
    name: str
    isDeleted: bool


class Price(BaseModel):
    currentPrice: float
    isIncludedInMenu: bool
    nextPrice: float | None
    nextIncludedInMenu: bool
    nextDatePrice: datetime.datetime | None


class PriceSize(BaseModel):
    sizeId: UUID | None
    price: Price


class Modifier(BaseModel):
    id: UUID
    defaultAmount: int | None
    minAmount: int
    maxAmount: int
    required: bool | None
    hideIfDefaultAmount: bool | None
    splittable: bool | None
    freeOfChargeAmount: int | None


class GroupModifier(Modifier):
    childModifiersHaveMinMaxRestrictions: bool | None
    childModifiers: list[Modifier]


class Product(BaseModel):
    fatAmount: float | None
    proteinsAmount: float | None
    carbohydratesAmount: float | None
    energyAmount: float | None
    fatFullAmount: float | None
    proteinsFullAmount: float | None
    carbohydratesFullAmount: float | None
    energyFullAmount: float | None
    weight: float | None
    groupId: UUID | None
    productCategoryId: UUID | None
    type: str | None  # dish | good | modifier
    orderItemType: str  # "Product" "Compound"
    modifierSchemaId: UUID | None
    modifierSchemaName: str | None
    splittable: bool
    measureUnit: str
    sizePrices: list[PriceSize]
    modifiers: list[Modifier]
    groupModifiers: list[GroupModifier]
    imageLinks: list[str]
    doNotPrintInCheque: bool
    parentGroup: UUID | None
    order: int
    fullNameEnglish: str | None
    useBalanceForSell: bool
    canSetOpenPrice: bool
    paymentSubject: str | None
    id: UUID
    code: str | None
    name: str
    description: str | None
    additionalInfo: str | None
    tags: list[str] | None
    isDeleted: bool
    seoDescription: str | None
    seoText: str | None
    seoKeywords: str | None
    seoTitle: str | None


class Size(BaseModel):
    id: UUID
    name: str
    priority: int | None
    isDefault: bool | None


class MenuResult(BaseModel):
    correlationId: UUID
    groups: list[ProductGroup]
    productCategories: list[ProductCategory]
    products: list[Product]
    sizes: list[Size]
    revision: int


class AccessTokenResult(BaseModel):
    correlationId: UUID
    token: str


class Error(BaseModel):
    correlationId: UUID
    errorDescription: str
    error: str | None
