#!/usr/bin/env python3
"""
Quick Start - Demo rápido del sistema
Ejecuta un ciclo completo de detección sin necesidad de credenciales reales
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import logging

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from scrapers.tesoro_scraper import TesoritacionScraper
from data.market_data import MarketDataProvider
from detector.signal_detector import LicitacionSignalDetector
from config import DETECTION_PARAMS

def main():
    print("=" * 80)
    print("🇦🇷 LICITACIÓN DETECTOR - QUICK START DEMO")
    print("=" * 80)
    print()
    
    # 1. Scraper de licitaciones
    print("📅 PASO 1: Buscando próximas licitaciones...")
    print("-" * 80)
    
    scraper = TesoritacionScraper()
    licitaciones = scraper.get_next_licitaciones(days_ahead=30)
    
    if licitaciones:
        print(f"✅ Encontradas {len(licitaciones)} licitaciones próximas:\n")
        for i, lic in enumerate(licitaciones[:3], 1):
            print(f"{i}. Fecha: {lic['fecha'].strftime('%Y-%m-%d')}")
            print(f"   Título: {lic['titulo'][:70]}...")
            if lic['instrumentos']:
                print(f"   Instrumentos: {', '.join(lic['instrumentos'][:5])}")
            print()
    else:
        print("ℹ️ No se encontraron licitaciones (usando simulación)")
        # Crear licitación simulada
        licitaciones = [{
            'fecha': datetime.now() + timedelta(days=2),
            'titulo': 'Licitación simulada para demo',
            'instrumentos': ['S17A6', 'S31L6', 'TZX26']
        }]
    
    print()
    
    # 2. Market Data
    print("📊 PASO 2: Obteniendo datos de mercado (simulados)...")
    print("-" * 80)
    
    market_data = MarketDataProvider(
        user="demo", 
        password="demo", 
        account="demo",
        environment="remarket"
    )
    
    ticker = licitaciones[0]['instrumentos'][0] if licitaciones[0].get('instrumentos') else "S17A6"
    
    data = market_data.get_market_data(ticker)
    print(f"Ticker: {ticker}")
    print(f"  Precio: ${data['last_price']:,.2f}")
    print(f"  Volumen: {data['volume']:,.0f}")
    print(f"  Spread: {data['spread_bps']:.2f} bps")
    
    vol_metrics = market_data.calculate_volume_metrics(ticker)
    print(f"\nMétricas de volumen:")
    print(f"  Promedio 30d: {vol_metrics['avg_volume_30d']:,.0f}")
    print(f"  Cambio vs promedio: {vol_metrics['volume_pct_change']:.1%}")
    print(f"  Tendencia: {vol_metrics['volume_trend']}")
    
    print()
    
    # 3. Detector de señales
    print("🧠 PASO 3: Generando señales de trading...")
    print("-" * 80)
    
    detector = LicitacionSignalDetector(market_data, DETECTION_PARAMS)
    
    lic_proxima = licitaciones[0]
    instrumentos = lic_proxima.get('instrumentos', ['S17A6', 'TZX26'])[:3]
    
    signals = detector.analyze_pre_licitacion(
        lic_proxima['fecha'],
        instrumentos
    )
    
    if signals:
        print(f"✅ Generadas {len(signals)} señales:\n")
        for signal in signals:
            print(f"{'='*80}")
            print(signal)
            print("\nRazones de la señal:")
            for reason in signal.reasoning:
                print(f"  • {reason}")
            print(f"\nMetadata:")
            print(f"  Días hasta licitación: {signal.metadata['days_until_licitacion']}")
            print(f"  Score de confianza: {signal.confidence_score:.1%}")
            print()
    else:
        print("ℹ️ No se generaron señales (condiciones de mercado no cumplen umbrales)")
    
    print()
    print("=" * 80)
    print("✅ Demo completado!")
    print("=" * 80)
    print()
    print("📋 Próximos pasos:")
    print("1. Revisar README.md para setup completo")
    print("2. Configurar credenciales en .env")
    print("3. Ejecutar: python main.py --mode paper --once")
    print()


if __name__ == "__main__":
    main()
