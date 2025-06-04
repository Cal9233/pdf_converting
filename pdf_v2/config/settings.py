"""Configuration settings for PDF to Excel converter v2."""

# Valid cardholder names (actual people who hold cards)
VALID_CARDHOLDERS = {
    'LUIS RODRIGUEZ',
    'JOSE RODRIGUEZ', 
    'ISABEL RODRIGUEZ',
    'GABRIEL TRUJILLO',
    'OCOMAR ENTERPRISES',
    'JUAN LUIS RODRIGUEZ',
    'PULAK UNG',
    'RODRIGUEZ GUTIERREZ'
}

# Common business/merchant indicators that should never be names
BUSINESS_INDICATORS = [
    'AIRLINES', 'AIRLINE', 'AIRWAYS', 'AIR',
    'CARD', 'CARDS', 'GIFT',
    'MERCHANDISE', 'GENERAL',
    'STORES', 'STORE', 'DISCOUNT',
    'VARIETY', 'RETAIL',
    'INC', 'LLC', 'CORP', 'CORPORATION',
    'COMPANY', 'CO.', 'LTD',
    'BANK', 'CREDIT', 'FINANCIAL',
    'SERVICES', 'SERVICE',
    'HOTEL', 'HOTELS', 'RESORT',
    'RESTAURANT', 'CAFE', 'COFFEE',
    'MARKET', 'MART', 'SHOP',
    'CENTER', 'CENTRE',
    'EXPRESS', 'PLUS', 'MOBILE',
    'ONLINE', 'DIGITAL', 'TECH',
    'AMERICA', 'AMERICAN', 'NATIONAL',
    'INTERNATIONAL', 'GLOBAL', 'WORLD'
]

# Date formats to try when parsing
DATE_FORMATS = [
    '%m/%d/%y',
    '%m/%d/%Y',
    '%d/%m/%y',
    '%d/%m/%Y',
    '%Y-%m-%d',
    '%m-%d-%Y',
    '%m-%d-%y'
]

# Transaction amount pattern
AMOUNT_PATTERN = r'\$?[\d,]+\.?\d{0,2}'

# Output settings
OUTPUT_DATE_FORMAT = '%m/%d/%Y'
EXCEL_COLUMN_WIDTHS = {
    'Name': 25,
    'Date': 12,
    'Merchant': 50,
    'Amount': 12
}