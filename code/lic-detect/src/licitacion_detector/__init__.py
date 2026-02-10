"""
Licitación Detector - Sistema de trading automatizado para arbitrar licitaciones
del Tesoro Nacional argentino.
"""

__version__ = "0.1.0"
__author__ = "Bruno - Teramot"
__email__ = "bruno@teramot.ai"

# Exponemos las clases principales para imports simplificados
from licitacion_detector.scrapers.tesoro_scraper import TesoritacionScraper
from licitacion_detector.data.market_data import MarketDataProvider
from licitacion_detector.detector.signal_detector import (
    LicitacionSignalDetector,
    SignalStrength,
    TradingSignal,
)

__all__ = [
    "TesoritacionScraper",
    "MarketDataProvider",
    "LicitacionSignalDetector",
    "SignalStrength",
    "TradingSignal",
]
