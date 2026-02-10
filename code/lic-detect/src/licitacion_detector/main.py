"""
Main - Orquestador del Licitación Detector
Ejecuta el loop principal de detección y trading
"""
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime, timedelta
import schedule
import argparse
import os

from licitacion_detector.config import (
    DETECTION_PARAMS, 
    TRADING_PARAMS, 
    LOG_CONFIG,
    ROFEX_USER,
    ROFEX_PASSWORD,
    ROFEX_ACCOUNT
)
from licitacion_detector.scrapers.tesoro_scraper import TesoritacionScraper
from licitacion_detector.data.market_data import MarketDataProvider
from licitacion_detector.detector.signal_detector import LicitacionSignalDetector


def setup_logging():
    """Configura logging del sistema"""
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(LOG_CONFIG['level'])
    
    # File handler con rotación
    file_handler = RotatingFileHandler(
        LOG_CONFIG['file'],
        maxBytes=LOG_CONFIG['max_bytes'],
        backupCount=LOG_CONFIG['backup_count']
    )
    file_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class LicitacionDetectorRunner:
    """Runner principal del sistema"""
    
    def __init__(self, mode: str = "live"):
        """
        Args:
            mode: 'live' para producción, 'paper' para simulación, 'backtest' para histórico
        """
        self.mode = mode
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Inicializar componentes
        self.logger.info(f"🚀 Inicializando Licitación Detector (modo: {mode})")
        
        self.tesoro_scraper = TesoritacionScraper()
        
        self.market_data = MarketDataProvider(
            user=ROFEX_USER,
            password=ROFEX_PASSWORD,
            account=ROFEX_ACCOUNT,
            environment="remarket" if mode != "live" else "live"
        )
        
        self.signal_detector = LicitacionSignalDetector(
            self.market_data,
            DETECTION_PARAMS
        )
        
        # Estado
        self.active_signals = []
        self.licitaciones_monitored = []
        self.last_scrape = None
    
    def run_detection_cycle(self):
        """Ejecuta un ciclo completo de detección"""
        self.logger.info("=" * 80)
        self.logger.info(f"🔄 Iniciando ciclo de detección - {datetime.now()}")
        self.logger.info("=" * 80)
        
        try:
            # 1. Actualizar calendario de licitaciones (cada 24hs)
            if not self.last_scrape or (datetime.now() - self.last_scrape) > timedelta(hours=24):
                self.logger.info("📅 Actualizando calendario de licitaciones...")
                self.licitaciones_monitored = self.tesoro_scraper.get_next_licitaciones(days_ahead=14)
                self.last_scrape = datetime.now()
                
                self.logger.info(f"✅ Encontradas {len(self.licitaciones_monitored)} licitaciones próximas:")
                for lic in self.licitaciones_monitored[:3]:
                    self.logger.info(f"   • {lic['fecha'].strftime('%Y-%m-%d')}: {lic['titulo'][:60]}...")
            
            # 2. Analizar cada licitación próxima
            for licitacion in self.licitaciones_monitored:
                dias_hasta = (licitacion['fecha'] - datetime.now()).days
                
                # Solo analizar si está en ventana de detección
                if 0 <= dias_hasta <= DETECTION_PARAMS['pre_licitacion_window']:
                    self.logger.info(f"\n🎯 Analizando licitación del {licitacion['fecha'].strftime('%Y-%m-%d')} "
                                   f"({dias_hasta} días)")
                    
                    # Obtener instrumentos (si no están, usar defaults)
                    instrumentos = licitacion.get('instrumentos', [])
                    if not instrumentos:
                        instrumentos = DETECTION_PARAMS['instrumentos_lecap'][:3]
                        self.logger.warning(f"No hay instrumentos específicos, usando: {instrumentos}")
                    
                    # Generar señales
                    new_signals = self.signal_detector.analyze_pre_licitacion(
                        licitacion['fecha'],
                        instrumentos
                    )
                    
                    if new_signals:
                        self.logger.info(f"✅ Generadas {len(new_signals)} nuevas señales")
                        for signal in new_signals:
                            self.logger.info(f"   {signal}")
                        
                        # Ejecutar trades (si estamos en modo live)
                        if self.mode == "live":
                            self.execute_signals(new_signals)
                        else:
                            self.logger.info("   [PAPER MODE - No se ejecutan trades reales]")
                        
                        self.active_signals.extend(new_signals)
                    else:
                        self.logger.info("ℹ️ No se generaron señales para esta licitación")
            
            # 3. Monitorear posiciones activas
            if self.active_signals:
                self.logger.info(f"\n📊 Posiciones activas: {len(self.active_signals)}")
                self.monitor_active_positions()
            else:
                self.logger.info("\nℹ️ No hay posiciones activas")
            
            self.logger.info("\n✅ Ciclo completado")
            
        except Exception as e:
            self.logger.error(f"❌ Error en ciclo de detección: {e}", exc_info=True)
    
    def execute_signals(self, signals):
        """Ejecuta trades basados en señales (STUB - implementar con broker real)"""
        self.logger.info(f"\n💼 Ejecutando {len(signals)} señales...")
        
        for signal in signals:
            try:
                # TODO: Implementar ejecución real con pyRofex
                # Por ahora solo logging
                
                direction = "SHORT" if signal.signal_strength.value < 0 else "LONG"
                size = self._calculate_position_size(signal)
                
                self.logger.info(f"   🔨 {direction} {signal.ticker}")
                self.logger.info(f"      Entry: ${signal.entry_price:,.2f}")
                self.logger.info(f"      Size: ${size:,.2f}")
                self.logger.info(f"      Target: ${signal.target_price:,.2f}")
                self.logger.info(f"      Stop: ${signal.stop_loss:,.2f}")
                
                # Aquí iría la ejecución real:
                # if signal.signal_strength.value < 0:
                #     # Short via repo o futuros
                #     order = rofex.send_order(...)
                # else:
                #     # Long directo
                #     order = rofex.send_order(...)
                
            except Exception as e:
                self.logger.error(f"Error ejecutando señal {signal.ticker}: {e}")
    
    def _calculate_position_size(self, signal) -> float:
        """Calcula tamaño de posición basado en risk management"""
        # Kelly criterion simplificado
        confidence = signal.confidence_score
        risk_per_trade = TRADING_PARAMS['position_size_pct']
        
        # Ajustar por confianza
        adjusted_size = risk_per_trade * confidence
        
        return TRADING_PARAMS['initial_capital_usd'] * adjusted_size
    
    def monitor_active_positions(self):
        """Monitorea posiciones abiertas y ejecuta stops/targets"""
        for signal in self.active_signals[:]:  # Copy para poder modificar
            current_data = self.market_data.get_market_data(signal.ticker)
            current_price = current_data.get('last_price')
            
            if not current_price:
                continue
            
            # Check stop loss
            if signal.signal_strength.value < 0:  # Short
                if current_price >= signal.stop_loss:
                    self.logger.warning(f"🛑 STOP LOSS alcanzado: {signal.ticker} @ ${current_price:,.2f}")
                    self.close_position(signal, "STOP_LOSS")
                elif current_price <= signal.target_price:
                    self.logger.info(f"🎯 TARGET alcanzado: {signal.ticker} @ ${current_price:,.2f}")
                    self.close_position(signal, "TARGET")
            else:  # Long
                if current_price <= signal.stop_loss:
                    self.logger.warning(f"🛑 STOP LOSS alcanzado: {signal.ticker} @ ${current_price:,.2f}")
                    self.close_position(signal, "STOP_LOSS")
                elif current_price >= signal.target_price:
                    self.logger.info(f"🎯 TARGET alcanzado: {signal.ticker} @ ${current_price:,.2f}")
                    self.close_position(signal, "TARGET")
    
    def close_position(self, signal, reason: str):
        """Cierra una posición"""
        self.logger.info(f"   Cerrando posición {signal.ticker} - Razón: {reason}")
        
        # TODO: Ejecutar cierre real con broker
        
        # Remover de activos
        if signal in self.active_signals:
            self.active_signals.remove(signal)
    
    def run_scheduler(self):
        """Ejecuta scheduler con tareas programadas"""
        self.logger.info("⏰ Configurando scheduler...")
        
        # Ciclo de detección cada hora en horario de mercado
        for hour in range(11, 19):  # 11:00 a 18:00
            schedule.every().day.at(f"{hour:02d}:00").do(self.run_detection_cycle)
        
        # Scraping de licitaciones una vez por día (8 AM)
        schedule.every().day.at("08:00").do(self.force_scrape_licitaciones)
        
        self.logger.info("✅ Scheduler configurado")
        self.logger.info("🏃 Entrando en loop principal...\n")
        
        # Loop principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check cada minuto
        except KeyboardInterrupt:
            self.logger.info("\n👋 Deteniendo detector...")
    
    def force_scrape_licitaciones(self):
        """Fuerza actualización de calendario"""
        self.last_scrape = None


def main():
    """Entry point principal"""
    parser = argparse.ArgumentParser(description='Licitación Detector - Sistema de trading automático')
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], default='paper',
                       help='Modo de ejecución')
    parser.add_argument('--once', action='store_true',
                       help='Ejecutar un solo ciclo y salir (no scheduler)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Banner
    print("=" * 80)
    print("🇦🇷 LICITACIÓN DETECTOR - Sistema de Trading Automático")
    print("=" * 80)
    print(f"Modo: {args.mode.upper()}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Inicializar runner
    runner = LicitacionDetectorRunner(mode=args.mode)
    
    if args.once:
        # Ejecutar un solo ciclo
        runner.run_detection_cycle()
    else:
        # Ejecutar scheduler continuo
        runner.run_scheduler()


if __name__ == "__main__":
    main()
