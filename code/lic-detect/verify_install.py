#!/usr/bin/env python3
"""
Script de verificación de instalación
Verifica que todos los módulos se importan correctamente
"""

def verify_installation():
    print("🔍 Verificando instalación de licitacion-detector...\n")
    
    errors = []
    
    # Test 1: Import del package principal
    print("1. Verificando package principal...")
    try:
        import licitacion_detector
        print(f"   ✅ licitacion_detector v{licitacion_detector.__version__}")
    except ImportError as e:
        errors.append(f"❌ Error importando licitacion_detector: {e}")
        print(f"   {errors[-1]}")
    
    # Test 2: Scrapers
    print("\n2. Verificando scrapers...")
    try:
        from licitacion_detector.scrapers.tesoro_scraper import TesoritacionScraper
        scraper = TesoritacionScraper()
        print("   ✅ TesoritacionScraper")
    except ImportError as e:
        errors.append(f"❌ Error importando scrapers: {e}")
        print(f"   {errors[-1]}")
    
    # Test 3: Market Data
    print("\n3. Verificando market data...")
    try:
        from licitacion_detector.data.market_data import MarketDataProvider
        provider = MarketDataProvider("test", "test", "test")
        print("   ✅ MarketDataProvider")
    except ImportError as e:
        errors.append(f"❌ Error importando market_data: {e}")
        print(f"   {errors[-1]}")
    
    # Test 4: Signal Detector
    print("\n4. Verificando signal detector...")
    try:
        from licitacion_detector.detector.signal_detector import LicitacionSignalDetector
        print("   ✅ LicitacionSignalDetector")
    except ImportError as e:
        errors.append(f"❌ Error importando signal_detector: {e}")
        print(f"   {errors[-1]}")
    
    # Test 5: Config
    print("\n5. Verificando configuración...")
    try:
        from licitacion_detector.config import DETECTION_PARAMS, TRADING_PARAMS
        print("   ✅ Configuración cargada")
        print(f"      - Umbrales: {len(DETECTION_PARAMS)} parámetros")
        print(f"      - Trading: {len(TRADING_PARAMS)} parámetros")
    except ImportError as e:
        errors.append(f"❌ Error importando config: {e}")
        print(f"   {errors[-1]}")
    
    # Test 6: Dependencies
    print("\n6. Verificando dependencias críticas...")
    deps = [
        ("requests", "HTTP requests"),
        ("bs4", "BeautifulSoup4"),
        ("pandas", "Data analysis"),
        ("numpy", "Numerical computing"),
        ("schedule", "Task scheduling"),
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            errors.append(f"❌ Falta dependencia: {name} ({module})")
            print(f"   {errors[-1]}")
    
    # Resumen
    print("\n" + "="*60)
    if errors:
        print(f"❌ Instalación incompleta - {len(errors)} errores:")
        for error in errors:
            print(f"   {error}")
        print("\n💡 Sugerencia: ejecutar 'pip install -e .'")
        return False
    else:
        print("✅ ¡Instalación verificada correctamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Configurar credenciales en .env")
        print("   2. Ejecutar: licitacion-quickstart")
        print("   3. O ejecutar: licitacion-detector --help")
        return True


if __name__ == "__main__":
    import sys
    success = verify_installation()
    sys.exit(0 if success else 1)
