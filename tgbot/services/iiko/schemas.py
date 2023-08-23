import datetime
import re
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import FieldValidationInfo


class ApiError(Exception):
    pass


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class Street(BaseModel):
    classifierId: str | None = None
    id: str | None = None
    name: str | None = None
    city: str | None = None


class Address(BaseModel):
    street: Street
    index: str | None = None
    house: str
    building: str | None = None
    flat: str | None = None
    entrance: str | None = None
    floor: str | None = None
    doorphone: str | None = None
    regionId: str | None = None


class DeliveryPoint(BaseModel):
    coordinates: Coordinates | None = None
    address: Address | None = None
    externalCartographyId: str | None = None
    comment: str | None = None


class OrderCustomer(BaseModel):
    id: str | None = None
    name: str | None = None
    surname: str | None = None
    comment: str | None = None
    birthday: str | None = None
    email: str | None = None
    shouldReceiveOrderStatusNotifications: bool | None = None
    gender: str = 'NotSpecified'
    type: str


class OrderGuests(BaseModel):
    count: int
    splitBetweenPersons: bool | None = None


class OrderItem(BaseModel):
    productId: str
    modifiers: None = None  # Not used
    price: float | None = None
    positionId: str | None = None
    type: str  # Product | Compound
    amount: float
    productSizeId: str | None = None
    comboInformation: None = None  # Not used
    comment: str | None = None


class OrderPayment(BaseModel):
    paymentTypeKind: str | None = None  # Cash, Card, IikoCard, External
    sum: float
    paymentTypeId: str
    isProcessedExternally: bool | None = None
    paymentAdditionalData: None = None
    isFiscalizedExternally: bool | None = None
    isPrepay: bool | None = None


class Order(BaseModel):
    menuId: str | None = None
    id: str | None = None
    externalNumber: int | None = None
    completeBefore: str | None = None
    phone: str
    orderTypeId: str | None = None
    orderServiceType: str | None = None
    deliveryPoint: DeliveryPoint | None = None
    comment: str | None = None
    customer: OrderCustomer | None = None
    guests: OrderGuests | None = None
    operatorId: str | None = None
    items: list[OrderItem]
    combos: None = None  # Not used
    payments: list[OrderPayment]
    tips: None = None  # Not used
    sourceKey: str | None = None
    discountsInfo: None = None  # Not used
    loyaltyInfo: None = None  # Not used
    chequeAdditionalInfo: None = None  # Not used
    externalData: None = None  # Not used
    marketingSourceId: str | None = None


class DeliveryCreate(BaseModel):
    organizationId: str
    terminalGroupId: str | None = None
    createOrderSettings: None = None  # not used
    order: Order


class DeliveryAddress(BaseModel):
    city: str | None = None
    streetName: str | None = None
    streetId: str | None = None
    house: str | None = None
    building: str | None = None
    index: str | None = None


class RestrictionsOrderItemModifier(BaseModel):
    id: str
    product: str | None = None
    amount: float


class RestrictionsOrderItem(BaseModel):
    id: str
    product: str
    amount: float
    modifiers: list[RestrictionsOrderItemModifier] | None = None


class SuitableTerminalGroupsRequest(BaseModel):
    organizationIds: list[str]
    deliveryAddress: DeliveryAddress | None = None
    orderLocation: Coordinates | None = None
    orderItems: list[RestrictionsOrderItem] | None = None
    isCourierDelivery: bool
    deliveryDate: str | None = None
    deliverySum: float | None = None
    discountSum: float | None = None


class AllowedItem(BaseModel):
    terminalGroupId: str
    organizationId: str
    deliveryDurationInMinutes: int
    zone: str | None = None
    deliveryServiceProductId: str | None = None


class RejectItemData(BaseModel):
    dateFrom: str | None = None
    dateTo: str | None = None
    allowedWeekDays: list[str] | None = None
    minSum: float | None = None


class RejectedItem(BaseModel):
    terminalGroupId: str | None = None
    organizationId: str | None = None
    zone: str | None = None
    rejectCode: str  # "Undefined" "SumIsLessThenMinimum" "DayOfWeekIsUnacceptable" "DeliveryTimeIsUnacceptable" "OutOfTerminalZone"
    rejectHint: str
    rejectItemData: RejectItemData


class SuitableTerminalGroupsResult(BaseModel):
    correlationId: str
    isAllowed: bool
    addressExternalId: str | None = None
    location: Coordinates | None = None
    allowedItems: list[AllowedItem]
    rejectedItems: list[RejectedItem]


class DynamicDiscount(BaseModel):
    manualConditionId: str
    Sum: float


class CalculateCheckinRequest(BaseModel):
    order: Order
    coupon: str | None = None
    # referrerId: str | None = None
    organizationId: str
    # terminalGroupId: str | None = None
    availablePaymentMarketingCampaignIds: list[str] | None = list()
    applicableManualConditions: list[str] | None = list()
    dynamicDiscounts: list[DynamicDiscount] | None = list()
    isLoyaltyTraceEnabled: bool


class Warning(BaseModel):
    Code: str | None = None
    ErrorCode: str | None = None
    Message: str | None = None


class WalletInfo(BaseModel):
    id: str
    maxSum: float
    canHoldMoney: bool


class AvailablePayment(BaseModel):
    id: str
    maxSum: float
    order: int
    walletInfos: list[WalletInfo]


class Discount(BaseModel):
    code: int
    positionId: str | None = None
    discountSum: float
    amount: float | None = None
    comment: str


class FreeProduct(BaseModel):
    id: str | None = None
    code: str | None = None
    size: list[str]


class FreeProductGroup(BaseModel):
    sourceActionId: str
    descriptionForUser: str | None = None
    products: list[FreeProduct]


class Upsale(BaseModel):
    sourceActionId: str
    suggestionText: str
    productCodes: list[str]


class GroupMapping(BaseModel):
    groupId: str
    itemId: str | None = None


class AvailableCombo(BaseModel):
    specificationId: str
    groupMapping: list[GroupMapping]


class LoyaltyProgramResult(BaseModel):
    marketingCampaignId: str
    name: str
    discounts: list[Discount]
    upsales: list[Upsale]
    freeProducts: list[FreeProductGroup]
    availableComboSpecifications: list[str]
    availableCombos: list[AvailableCombo]
    needToActivateCertificate: bool


class CalculateCheckinResult(BaseModel):
    loyaltyTrace: str | None = None
    validationWarnings: list[str]
    Warnings: list[Warning]
    availablePayments: list[AvailablePayment]
    loyaltyProgramResults: list[LoyaltyProgramResult]


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


class Table(BaseModel):
    id: UUID
    number: int
    name: str
    seatingCapacity: int
    revision: int
    isDeleted: bool


class RestaurantSection(BaseModel):
    id: UUID
    terminalGroupId: UUID
    name: str
    tables: list[Table]
    # schema: ...  # Too big object


class TablesResult(BaseModel):
    correlationId: UUID
    revision: int
    restaurantSections: list[RestaurantSection]


class GuestWallet(BaseModel):
    id: UUID
    name: str
    type: int
    balance: float


class CreateOrUpdateCustomer(BaseModel):
    id: str | None = None
    referrerId: str | None = None
    name: str | None = None
    surname: str | None = None
    middleName: str | None = None
    phone: str | None = None
    birthday: str | None = None
    email: str | None = None
    sex: int = 0  # 0 - not specified, 1 - male, 2 - female
    consentStatus: int = 0  # 0 - unknown, 1 - given, 2 - revoked
    shouldReceivePromoActionsInfo: bool | None = None
    userData: str | None = None
    organizationId: str | None = None

    @field_validator('sex', 'consentStatus')
    @classmethod
    def check_sex_and_consent(cls, value: int, info: FieldValidationInfo):
        assert value in (0, 1, 2), f'{info.field_name} must be 0, 1 or 2'
        return value

    @field_validator('birthday', mode='before')
    @classmethod
    def convert_to_str(cls, value):
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        elif isinstance(value, str):
            pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$'
            if re.match(pattern, value):
                return value
            else:
                assert False, 'Birthday must match the format "yyyy-MM-dd HH:mm:ss.fff"'

        return value


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
    deliveryServiceType: str | None  # “CourierOnly” or “SelfServiceOnly” or “CourierAndSelfService”
    defaultCallCenterPaymentTypeId: UUID | None
    orderItemCommentEnabled: bool | None
    inn: str | None
    addressFormatType: str  # “Legacy” or “City” or “International” or “IntNoPostcode”
    isConfirmationEnabled: bool | None
    confirmAllowedIntervalInMinutes: int | None
    isCloud: bool
    isAnonymousGuestsAllowed: bool
    addressLookup: list[str]  # Items Enum: “DaData“ “GetAddress“


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


class PaymentType(BaseModel):
    id: str | None = None
    code: str | None = None
    name: str | None = None
    comment: str | None = None
    combinable: bool
    externalRevision: int | None = None
    applicableMarketingCampaigns: list[str]
    isDeleted: bool
    printCheque: bool
    paymentProcessingType: str | None = None  # “External” “Internal” “Both”
    paymentTypeKind: str | None = None  # “Unknown” “Cash” “Card” “Credit” “Writeoff” “Voucher” “External” “IikoCard"
    terminalGroups: list[TerminalGroupItem]


class Guests(BaseModel):
    count: int


class CreateReserveRequest(BaseModel):
    organizationId: str
    terminalGroupId: str
    id: str | None = None
    externalNumber: str | None = None
    order: Order | None = None
    customer: OrderCustomer
    phone: str
    comment: str | None = None
    durationInMinutes: int
    shouldRemind: bool
    tableIds: list[str]
    estimatedStartTime: str
    transportToFrontTimeout: int | None = None
    guests: Guests | None = None
    eventType: str | None = None


class ErrorInfo(BaseModel):
    code: str
    message: str | None = None
    description: str | None = None
    additionalData: Any | None = None


class ReserveInfo(BaseModel):
    id: str
    organizationId: str
    externalNumber: str | None = None
    timestamp: int
    creationStatus: str  # "Success" "InProgress" "Error"
    isDeleted: bool
    errorInfo: ErrorInfo | None = None
    reserve: None = None  # Not used


class CreateReserveResult(BaseModel):
    correlationId: str
    reserveInfo: ReserveInfo


class Reserve(BaseModel):
    id: str
    tableIds: list[str]
    estimatedStartTime: str
    durationInMinutes: int
    guestsCount: int


class ReservesResult(BaseModel):
    correlationId: str
    reserves: list[Reserve]


class PaymentTypesResult(BaseModel):
    correlationId: UUID
    paymentTypes: list[PaymentType]


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
    orderItemType: str  # “Product”, “Compound”
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
