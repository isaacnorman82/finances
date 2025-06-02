import logging

from fastapi import APIRouter

from backend import api_models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metadata", tags=["Metadata"])

API_VERSION = "1.6.0"


@router.get("/version/", summary="List API version")
def api_get_version():
    return {"api_version": API_VERSION}


@router.get(
    "/ingest-types/",
    summary="Get the supported ingest types",
)
def api_get_ingest_types():
    return [x.value for x in api_models.IngestType]


@router.get(
    "/cpi/",
    summary="Get inflation rates (CPI)",
)
def api_get_cpi():
    # https://www.rateinflation.com/inflation-rate/uk-historical-inflation-rate/
    return {
        1989: 0.05216,
        1990: 0.06999,
        1991: 0.07519,
        1992: 0.04232,
        1993: 0.02533,
        1994: 0.01994,
        1995: 0.0263,
        1996: 0.02425,
        1997: 0.01825,
        1998: 0.01557,
        1999: 0.01329,
        2000: 0.00796,
        2001: 0.01234,
        2002: 0.01259,
        2003: 0.01362,
        2004: 0.01344,
        2005: 0.02057,
        2006: 0.02329,
        2007: 0.02323,
        2008: 0.03602,
        2009: 0.02165,
        2010: 0.03298,
        2011: 0.04464,
        2012: 0.02828,
        2013: 0.02565,
        2014: 0.01461,
        2015: 0.0004,
        2016: 0.0066,
        2017: 0.02683,
        2018: 0.02478,
        2019: 0.01791,
        2020: 0.00851,
        2021: 0.02588,
        2022: 0.09067,
        2023: 0.07303,
        2024: 0.02530,
    }
