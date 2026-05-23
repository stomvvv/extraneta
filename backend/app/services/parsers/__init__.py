from app.models.booking import OTASource
from app.services.parsers.base import BaseParser, ParseResult, ParsedBooking
from app.services.parsers.yandex import YandexParser
from app.services.parsers.ostrovok import OstrovokParser
from app.services.parsers.bronevoy import BronevoyParser
from app.services.parsers.tinkoff import TinkoffParser
from app.services.parsers.gis2 import Gis2Parser
from app.services.parsers.hotel101 import Hotel101Parser
from app.services.parsers.academservis import AcademservisParser

PARSER_REGISTRY: dict[OTASource, type[BaseParser]] = {
    OTASource.yandex: YandexParser,
    OTASource.ostrovok: OstrovokParser,
    OTASource.bronevoy: BronevoyParser,
    OTASource.tinkoff: TinkoffParser,
    OTASource.gis2: Gis2Parser,
    OTASource.hotel101: Hotel101Parser,
    OTASource.academservis: AcademservisParser,
}


def get_parser(ota: OTASource) -> BaseParser:
    parser_class = PARSER_REGISTRY.get(ota)
    if not parser_class:
        raise ValueError(f"No parser registered for OTA: {ota}")
    return parser_class()


__all__ = ["get_parser", "PARSER_REGISTRY", "ParseResult", "ParsedBooking"]
