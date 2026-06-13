from parsers.yandex import YandexParser
from parsers.ostrovok import OstrovokParser
from parsers.bronevic import BronevicParser
from parsers.tinkoff import TinkoffParser
from parsers.gis2 import Gis2Parser
from parsers.hotel101 import Hotel101Parser
from parsers.academservis import AcademservisParser
from parsers.auto import AutoParser

PARSERS = {
    "yandex": YandexParser,
    "ostrovok": OstrovokParser,
    "bronevic": BronevicParser,
    "tinkoff": TinkoffParser,
    "2gis": Gis2Parser,
    "101hotel": Hotel101Parser,
    "academservis": AcademservisParser,
    "auto": AutoParser,
}

OTA_NAMES = {
    "yandex": "Яндекс Путешествия",
    "ostrovok": "Ostrovok.ru",
    "bronevic": "Броневик",
    "tinkoff": "Тинькофф Путешествия",
    "2gis": "2ГИС",
    "101hotel": "101отель",
    "academservis": "Academservis",
}

DEFAULT_COMMISSION_RATES = {
    "yandex": 18.0,
    "ostrovok": 15.0,
    "bronevic": 12.0,
    "tinkoff": 20.0,
    "2gis": 10.0,
    "101hotel": 15.0,
    "academservis": 12.0,
}
