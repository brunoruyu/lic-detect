"""
Signal Detector - Detecta señales pre-licitación combinando
datos de mercado y calendario de licitaciones
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Fuerza de la señal detectada"""
    STRONG_BEARISH = -2  # Vender agresivo
    WEAK_BEARISH = -1    # Vender conservador
    NEUTRAL = 0          # No operar
    WEAK_BULLISH = 1     # Comprar conservador
    STRONG_BULLISH = 2   # Comprar agresivo


@dataclass
class TradingSignal:
    """Señal de trading generada"""
    timestamp: datetime
    ticker: str
    signal_strength: SignalStrength
    confidence_score: float  # 0-1
    entry_price: float
    target_price: float
    stop_loss: float
    reasoning: List[str]  # Lista de razones
    metadata: Dict
    
    def __str__(self):
        direction = "📉 SHORT" if self.signal_strength.value < 0 else "📈 LONG"
        return (f"{direction} {self.ticker} @ ${self.entry_price:,.2f} | "
                f"Confianza: {self.confidence_score:.1%} | "
                f"Target: ${self.target_price:,.2f} | "
                f"Stop: ${self.stop_loss:,.2f}")


class LicitacionSignalDetector:
    """
    Detector de señales pre-licitación
    
    Combina múltiples indicadores para generar señales de alta confianza:
    1. Proximidad a licitación
    2. Caída de volumen
    3. Ampliación de spreads
    4. Nerviosismo en dólar MEP-oficial
    5. Comportamiento BCRA
    """
    
    def __init__(self, market_data_provider, config: Dict):
        self.market_data = market_data_provider
        self.config = config
        
        # Umbrales de detección
        self.volume_drop_threshold = config.get('volume_drop_threshold', 0.30)
        self.spread_increase_threshold = config.get('spread_increase_threshold', 0.15)
        self.mep_spread_threshold = config.get('mep_oficial_threshold', 0.015)
        self.min_confidence = config.get('min_confidence_score', 0.75)
        
        # Window de análisis
        self.pre_licitacion_window = config.get('pre_licitacion_window', 3)  # días
    
    def analyze_pre_licitacion(self, 
                               licitacion_fecha: datetime,
                               instrumentos: List[str]) -> List[TradingSignal]:
        """
        Analiza mercado previo a licitación y genera señales
        
        Args:
            licitacion_fecha: Fecha de la licitación
            instrumentos: Lista de tickers a analizar
        
        Returns:
            Lista de señales de trading
        """
        signals = []
        
        # Calcular días hasta licitación
        days_until = (licitacion_fecha - datetime.now()).days
        
        # Solo analizar si estamos en ventana pre-licitación
        if days_until > self.pre_licitacion_window or days_until < 0:
            logger.info(f"Fuera de ventana pre-licitación (días: {days_until})")
            return signals
        
        logger.info(f"🔍 Analizando señales para licitación del {licitacion_fecha.strftime('%Y-%m-%d')} "
                   f"({days_until} días)")
        
        for ticker in instrumentos:
            try:
                signal = self._analyze_ticker(ticker, days_until)
                
                if signal and signal.confidence_score >= self.min_confidence:
                    signals.append(signal)
                    logger.info(f"✅ Señal generada: {signal}")
                else:
                    logger.debug(f"⚠️ Señal rechazada para {ticker} (confianza baja)")
                    
            except Exception as e:
                logger.error(f"Error analizando {ticker}: {e}")
                continue
        
        return signals
    
    def _analyze_ticker(self, ticker: str, days_until_licitacion: int) -> Optional[TradingSignal]:
        """Analiza un ticker individual y genera señal"""
        
        # 1. Obtener market data
        current_data = self.market_data.get_market_data(ticker)
        if not current_data or not current_data.get('last_price'):
            logger.warning(f"No hay datos para {ticker}")
            return None
        
        # 2. Calcular indicadores
        volume_metrics = self.market_data.calculate_volume_metrics(ticker)
        spread_metrics = self.market_data.calculate_spread_metrics(ticker)
        dollar_spread = self.market_data.get_dollar_spread()
        
        # 3. Evaluar cada señal
        signals_detected = []
        reasoning = []
        
        # SEÑAL 1: Caída de volumen (típico pre-licitación)
        if volume_metrics['volume_pct_change'] < -self.volume_drop_threshold:
            signals_detected.append(-1)  # Bearish
            reasoning.append(
                f"📉 Volumen cayó {abs(volume_metrics['volume_pct_change']):.1%} vs promedio "
                f"(threshold: {self.volume_drop_threshold:.1%})"
            )
        
        # SEÑAL 2: Ampliación de spreads (menos liquidez)
        if spread_metrics['spread_pct_increase'] > self.spread_increase_threshold:
            signals_detected.append(-0.8)  # Moderado bearish
            reasoning.append(
                f"📏 Spread aumentó {spread_metrics['spread_pct_increase']:.1%} "
                f"(percentil: {spread_metrics['spread_percentile']:.0f})"
            )
        
        # SEÑAL 3: Nerviosismo en dólar (MEP-oficial)
        if dollar_spread['spread_pct'] > self.mep_spread_threshold:
            signals_detected.append(-0.6)  # Leve bearish
            reasoning.append(
                f"💵 Spread MEP-Oficial en {dollar_spread['spread_pct']:.2%} "
                f"(threshold: {self.mep_spread_threshold:.2%})"
            )
        
        # SEÑAL 4: Proximidad temporal (más cerca = más bearish)
        time_factor = 1 - (days_until_licitacion / self.pre_licitacion_window)
        if time_factor > 0.5:  # Dentro de 1.5 días
            signals_detected.append(-time_factor)
            reasoning.append(
                f"⏰ Licitación en {days_until_licitacion} días (factor: {time_factor:.2f})"
            )
        
        # Si no hay señales, retornar None
        if not signals_detected:
            logger.debug(f"No hay señales para {ticker}")
            return None
        
        # 4. Calcular señal agregada y confianza
        avg_signal = np.mean(signals_detected)
        confidence = len(signals_detected) / 4  # Máximo 4 señales posibles
        
        # Ajustar confianza por calidad de señales
        strong_signals = sum(1 for s in signals_detected if abs(s) > 0.7)
        confidence = confidence * (0.7 + 0.3 * (strong_signals / len(signals_detected)))
        
        # 5. Determinar strength
        if avg_signal <= -0.7:
            signal_strength = SignalStrength.STRONG_BEARISH
        elif avg_signal <= -0.3:
            signal_strength = SignalStrength.WEAK_BEARISH
        elif avg_signal >= 0.7:
            signal_strength = SignalStrength.STRONG_BULLISH
        elif avg_signal >= 0.3:
            signal_strength = SignalStrength.WEAK_BULLISH
        else:
            signal_strength = SignalStrength.NEUTRAL
        
        # 6. Calcular precios (entry, target, stop)
        entry_price = current_data['last_price']
        
        if signal_strength.value < 0:  # Short position
            # Target: -2.5% (licitación exitosa)
            target_price = entry_price * 0.975
            # Stop: +1.5% (por si licitación falla)
            stop_loss = entry_price * 1.015
        else:  # Long position (post-licitación)
            target_price = entry_price * 1.025
            stop_loss = entry_price * 0.985
        
        # 7. Crear señal
        signal = TradingSignal(
            timestamp=datetime.now(),
            ticker=ticker,
            signal_strength=signal_strength,
            confidence_score=confidence,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            reasoning=reasoning,
            metadata={
                'days_until_licitacion': days_until_licitacion,
                'volume_metrics': volume_metrics,
                'spread_metrics': spread_metrics,
                'dollar_spread': dollar_spread,
                'avg_signal_score': avg_signal,
            }
        )
        
        return signal
    
    def evaluate_post_licitacion(self, 
                                licitacion_result: Dict,
                                active_signals: List[TradingSignal]) -> List[Dict]:
        """
        Evalúa señales después de publicarse resultados de licitación
        
        Args:
            licitacion_result: {
                'fecha': datetime,
                'rollover_pct': float,  # % renovado
                'instrumentos': List[str]
            }
            active_signals: Lista de señales abiertas
        
        Returns:
            Lista de acciones: [{'signal': TradingSignal, 'action': 'CLOSE'|'HOLD', 'reason': str}]
        """
        actions = []
        rollover = licitacion_result.get('rollover_pct', 0)
        
        logger.info(f"📊 Evaluando post-licitación: Rollover {rollover:.1%}")
        
        for signal in active_signals:
            # Lógica de cierre basada en rollover
            if rollover >= 0.95:
                # Licitación muy exitosa → cerrar shorts, puede haber rally
                if signal.signal_strength.value < 0:
                    actions.append({
                        'signal': signal,
                        'action': 'CLOSE',
                        'reason': f"Rollover excelente ({rollover:.1%}) - Cerrar short"
                    })
                else:
                    actions.append({
                        'signal': signal,
                        'action': 'HOLD',
                        'reason': f"Rollover excelente - Mantener long"
                    })
            
            elif rollover >= 0.85:
                # Licitación buena → cerrar parcialmente
                if signal.signal_strength.value < 0:
                    actions.append({
                        'signal': signal,
                        'action': 'PARTIAL_CLOSE',
                        'partial_pct': 0.5,
                        'reason': f"Rollover bueno ({rollover:.1%}) - Cerrar 50%"
                    })
                else:
                    actions.append({
                        'signal': signal,
                        'action': 'HOLD',
                        'reason': f"Rollover aceptable"
                    })
            
            else:
                # Licitación débil → mantener shorts, cerrar longs
                if signal.signal_strength.value < 0:
                    actions.append({
                        'signal': signal,
                        'action': 'HOLD',
                        'reason': f"Rollover débil ({rollover:.1%}) - Mantener short"
                    })
                else:
                    actions.append({
                        'signal': signal,
                        'action': 'CLOSE',
                        'reason': f"Rollover débil - Cerrar long"
                    })
        
        return actions


# ==================== TESTING ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock data provider
    from licitacion_detector.data.market_data import MarketDataProvider
    
    print("🧠 Testing Signal Detector\n")
    
    # Inicializar
    market_data = MarketDataProvider(
        user="demo", password="demo", account="demo", environment="remarket"
    )
    
    config = {
        'volume_drop_threshold': 0.30,
        'spread_increase_threshold': 0.15,
        'mep_oficial_threshold': 0.015,
        'min_confidence_score': 0.70,
        'pre_licitacion_window': 3,
    }
    
    detector = LicitacionSignalDetector(market_data, config)
    
    # Simular licitación en 2 días
    licitacion_fecha = datetime.now() + timedelta(days=2)
    instrumentos = ["S17A6", "S31L6", "TZX26"]
    
    print(f"📅 Licitación simulada: {licitacion_fecha.strftime('%Y-%m-%d')}\n")
    
    # Generar señales
    signals = detector.analyze_pre_licitacion(licitacion_fecha, instrumentos)
    
    print(f"\n🎯 Señales generadas: {len(signals)}\n")
    for sig in signals:
        print(f"{sig}\n")
        print("Razones:")
        for reason in sig.reasoning:
            print(f"  • {reason}")
        print(f"Metadata: Confianza={sig.confidence_score:.1%}, "
              f"Días={sig.metadata['days_until_licitacion']}")
        print("-" * 80)
        print()
    
    # Simular post-licitación
    if signals:
        print("\n📊 Simulando resultado de licitación (rollover 92%)...\n")
        
        result = {
            'fecha': licitacion_fecha,
            'rollover_pct': 0.92,
            'instrumentos': instrumentos
        }
        
        actions = detector.evaluate_post_licitacion(result, signals)
        
        print(f"⚡ Acciones recomendadas: {len(actions)}\n")
        for action in actions:
            print(f"Ticker: {action['signal'].ticker}")
            print(f"Acción: {action['action']}")
            print(f"Razón: {action['reason']}")
            print("-" * 80)
