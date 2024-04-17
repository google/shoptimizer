# coding=utf-8
# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared constants used for optimizer modules in the Shoptimizer API."""
from typing import Set, Tuple

LANGUAGE_CODE_DE: str = 'de'
LANGUAGE_CODE_EN: str = 'en'
LANGUAGE_CODE_FR: str = 'fr'
LANGUAGE_CODE_ID: str = 'id'
LANGUAGE_CODE_JA: str = 'ja'
LANGUAGE_CODE_VI: str = 'vi'
LANGUAGE_CODE_KO: str = 'ko'

COUNTRY_CODE_DE: str = 'de'
COUNTRY_CODE_FR: str = 'fr'
COUNTRY_CODE_ID: str = 'id'
COUNTRY_CODE_IN: str = 'in'
COUNTRY_CODE_JP: str = 'jp'
COUNTRY_CODE_US: str = 'us'
COUNTRY_CODE_VN: str = 'vn'
COUNTRY_CODE_KR: str = 'kr'

CURRENCY_CODE_EUR: str = 'EUR'
CURRENCY_CODE_IDR: str = 'IDR'
CURRENCY_CODE_INR: str = 'INR'
CURRENCY_CODE_JPY: str = 'JPY'
CURRENCY_CODE_USD: str = 'USD'
CURRENCY_CODE_VND: str = 'VND'
CURRENCY_CODE_KRW: str = 'KRW'

DEFAULT_LANG: str = LANGUAGE_CODE_EN
DEFAULT_COUNTRY: str = COUNTRY_CODE_US
DEFAULT_CURRENCY: str = CURRENCY_CODE_USD

MAX_ALTERNATE_IMAGE_URLS: int = 10
MAX_IMAGE_URL_LENGTH: int = 2000
MAX_IMAGE_FILE_SIZE_BYTES: int = 16000000  # 16MB
VALID_IMAGE_URL_FILE_SUFFIXES: Tuple[str,
                                     ...] = ('.JPG', '.JPEG', '.WEBP', '.PNG',
                                             '.GIF', '.BMP', '.TIF', '.TIFF')

MAX_COLOR_COUNT: int = 3
MAX_COLOR_STR_LENGTH_FOR_EACH: int = 40
MAX_COLOR_STR_LENGTH_IN_TOTAL: int = 100

CLOTHING_SIZES_CHARS_SLASH_SEPARATOR = r'(\b([0-9]{1,3})?(X{0,3})(S{1,2})\b|\bM{1}\b|\b([0-9]{1,3})?(X{0,2})(L{1,2})\b)(\/(([0-9]{1,3})?(X{0,3})(S{1,2})\b|M{1}\b|([0-9]{1,3})?(X{0,2})(L{1,2})\b))*'
CLOTHING_SIZES_CHARS_REGEX_RANGE = r'((\b([0-9]{1,3})?[X]*(S{1,2}\b)?(\bM{1}\b)?\b([0-9]{1,3})?[X]*(L{1,2}\b)?)(-(\b([0-9]{1,3})?[X]*(S{1,2}\b)?(\bM{1}\b)?\b([0-9]{1,3})?[X]*(L{1,2})?))?)'
CLOTHING_SIZES_REGEX_WORDS = r'((X|EXTRA)?[\s|-]?SMALL\/?\b|(X|EXTRA)?[\s|-]?MEDIUM\/?\b|(X|EXTRA)?[\s|-]?LARGE\/?\b|OSFA\/?\b|\bOS\/?\b)'
CLOTHING_SIZES_JA: Tuple[str,
                         ...] = ('XXS', 'XS', 'S', 'M', 'L', 'LL', 'XL', 'XXL')
CLOTHING_SIZES_KO: Tuple[str, ...] = ('XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL')
NUMERIC_CLOTHING_SIZES_JA_REGEX = r'\d*\.?\d+(-?\d+)?(\.?\d+)?\s?(cm|centimeters|センチ|センチメートル|mm|ミリメートル|ミリ|inches|inch|in|インチ|years|yo|歳)?'
NUMERIC_CLOTHING_SIZES_KO_REGEX = r'\d*\.?\d+(-?\d+)?(\.?\d+)?\s?(cm|centimeters|센티|센티미터|mm|밀리미터|인치|inches|inch|in|years|yo|살)?'
ALPHABETIC_CLOTHING_SIZES_JP_UNISIZE_MULTI_WORD: Tuple[str, ...] = ('フリーサイズ',
                                                                    'Free Size',
                                                                    '00(FREE)',
                                                                    'F/FREE',
                                                                    'One size')
ALPHABETIC_CLOTHING_SIZES_KR_UNISIZE_MULTI_WORD: Tuple[str, ...] = (
    'Free Size',
    'FREESIZE',
    '00(FREE)',
    'F/FREE',
    'One size',
    'Free사이즈',
    'Free 사이즈',
    '프리사이즈',
    '프리 사이즈',
    '원사이즈',
    '원 사이즈',
)
ALPHABETIC_CLOTHING_SIZES_JP_UNISIZE_SINGLE_WORD: Tuple[str,
                                                        ...] = ('フリー', 'FREE',
                                                                'free',
                                                                'unisize',
                                                                '1_size')
ALPHABETIC_CLOTHING_SIZES_KR_UNISIZE_SINGLE_WORD: Tuple[str, ...] = (
    '프리',
    'FREE',
    'free',
    'unisize',
    '1_size',
)
ALPHABETIC_CLOTHING_SIZES_EN_UNISIZE: Tuple[str, ...] = ('One size fits all',
                                                         'One size')

MINIMUM_SHOE_SIZE_JP: float = 10
MAXIMUM_SHOE_SIZE_JP: float = 35

MINIMUM_SHOE_SIZE_US: float = 4
MAXIMUM_SHOE_SIZE_US: float = 16

MINIMUM_SHOE_SIZE_KR: float = 100
MAXIMUM_SHOE_SIZE_KR: float = 370

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_KEYWORDS: Set[str] = {
    'Apparel & Accessories',
    'ファッション・アクセサリー',
    'Pakaian & Aksesori',
    '의류/액세서리',
}

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_IDS: Set[str] = {
    '166',
    '184',
    '5192',
    '500008',
    '8017',
    '5907',
    '5426',
    '8200',
    '500118',
    '8018',
    '7304',
    '5387',
    '5193',
    '5194',
    '188',
    '189',
    '6463',
    '192',
    '196',
    '194',
    '191',
    '197',
    '190',
    '200',
    '5122',
    '7471',
    '5123',
    '6870',
    '201',
    '6551',
    '3032',
    '6170',
    '6169',
    '2668',
    '6552',
    '5841',
    '175',
    '6277',
    '6460',
    '167',
    '5942',
    '5443',
    '5446',
    '193',
    '179',
    '499972',
    '178',
    '177',
    '6985',
    '176',
    '180',
    '7230',
    '5207',
    '7133',
    '3913',
    '168',
    '171',
    '8451',
    '181',
    '7305',
    '7307',
    '7306',
    '2477',
    '5914',
    '4057',
    '1483',
    '6183',
    '1948',
    '502988',
    '5915',
    '1662',
    '2020',
    '7054',
    '5422',
    '5623',
    '5626',
    '5625',
    '5624',
    '169',
    '502987',
    '1893',
    '6268',
    '5941',
    '5390',
    '5687',
    '5686',
    '5688',
    '5685',
    '173',
    '5114',
    '170',
    '1786',
    '4179',
    '6238',
    '6984',
    '1604',
    '203',
    '5598',
    '5909',
    '5506',
    '1831',
    '3066',
    '5514',
    '5182',
    '7132',
    '5250',
    '5490',
    '5344',
    '207',
    '1581',
    '6229',
    '2331',
    '6228',
    '5322',
    '3951',
    '499979',
    '5460',
    '5462',
    '5552',
    '5461',
    '5517',
    '6006',
    '7003',
    '5463',
    '5555',
    '5378',
    '5379',
    '5697',
    '3455',
    '6087',
    '3729',
    '3188',
    '3128',
    '1594',
    '1516',
    '1580',
    '5183',
    '7313',
    '212',
    '208',
    '5513',
    '2580',
    '5713',
    '2302',
    '204',
    '5441',
    '5329',
    '5330',
    '182',
    '5549',
    '5412',
    '5622',
    '5425',
    '5410',
    '5408',
    '5411',
    '5424',
    '5409',
    '5423',
    '5621',
    '2306',
    '3598',
    '3888',
    '3724',
    '5564',
    '3379',
    '3683',
    '3439',
    '3958',
    '3852',
    '3253',
    '4003',
    '3191',
    '5878',
    '5484',
    '206',
    '2292',
    '3414',
    '5949',
    '7235',
    '2396',
    '7236',
    '7237',
    '2271',
    '213',
    '1807',
    '2745',
    '5327',
    '215',
    '5834',
    '2562',
    '214',
    '7207',
    '7209',
    '7208',
    '7211',
    '7210',
    '2963',
    '1772',
    '2563',
    '1675',
    '2160',
    '1578',
    '209',
    '5388',
    '8248',
    '6031',
    '7281',
    '6227',
    '5483',
    '8149',
    '5676',
    '5343',
    '5684',
    '5680',
    '5682',
    '5683',
    '5679',
    '5681',
    '5673',
    '5677',
    '5678',
    '5674',
    '211',
    '187',
    '1933',
    '7078',
    '5385',
    '5567',
    '2427',
    '185',
}

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_CLOTHING_KEYWORDS: Set[str] = {
    'Apparel & Accessories > Clothing',
    'ファッション・アクセサリー > 衣料品',
    '의류/액세서리 > 의류',
}

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_CLOTHING_IDS: Set[str] = {
    '1604',
    '5322',
    '5697',
    '3128',
    '3455',
    '3188',
    '6087',
    '3729',
    '5378',
    '499979',
    '3951',
    '5460',
    '5462',
    '5461',
    '5552',
    '5379',
    '5517',
    '6006',
    '7003',
    '5463',
    '5555',
    '182',
    '5408',
    '5549',
    '5424',
    '5425',
    '5622',
    '5412',
    '5423',
    '5409',
    '5410',
    '5411',
    '5621',
    '2271',
    '5182',
    '5250',
    '5490',
    '7132',
    '203',
    '5506',
    '5598',
    '5514',
    '3066',
    '5909',
    '1831',
    '7313',
    '204',
    '212',
    '207',
    '1581',
    '5344',
    '208',
    '5713',
    '5513',
    '2580',
    '2302',
    '1594',
    '5183',
    '1516',
    '1580',
    '211',
    '5388',
    '6031',
    '5674',
    '6227',
    '5673',
    '5343',
    '5483',
    '8149',
    '8248',
    '7281',
    '5676',
    '213',
    '7207',
    '7208',
    '7211',
    '7210',
    '7209',
    '214',
    '215',
    '5327',
    '1772',
    '2563',
    '2160',
    '1675',
    '1807',
    '2963',
    '1578',
    '209',
    '2745',
    '2562',
    '5834',
    '2306',
    '5484',
    '5878',
    '7235',
    '7237',
    '2396',
    '7236',
    '5949',
    '206',
    '3414',
    '3598',
    '3191',
    '3439',
    '3683',
    '3724',
    '3888',
    '3958',
    '4003',
    '3253',
    '5564',
    '3379',
    '3852',
    '2292',
    '5441',
    '5330',
    '5329',
}

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_SHOES_KEYWORDS: Set[str] = {
    'Apparel & Accessories > Shoes',
    'ファッション・アクセサリー > 靴',
    '의류/액세서리 > 신발',
}

GOOGLE_PRODUCT_CATEGORY_APPAREL_ACCESSORIES_SHOES_IDS: Set[str] = {
    '187',
}

TITLE_CHARS_VISIBLE_TO_USER_JA: int = 18
TITLE_CHARS_VISIBLE_TO_USER_EN: int = 25
