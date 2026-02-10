"""
Market Data Module - Integración con Rofex/Primary
Obtiene precios, volúmenes, spreads en tiempo real
"""
try:
    import pyRofex as rofex
    PYROFEX_AVAILABLE = True
except ImportError:
    PYROFEX_AVAILABLE = False
    print("⚠️ pyRofex no instalado - usando datos simulados")

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from collections import deque
import time

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Provider de datos de mercado para detección de señales"""
    
    def __init__(self, user: str, password: str, account: str, environment: str = "remarket"):
        """
        Args:
            environment: 'live' para producción, 'remarket' para demo
        """
        self.user = user
        self.password = password
        self.account = account
        self.environment = environment
        self.connected = False
        
        # Cache de datos (rolling window de 30 días)
        self.price_history = {}  # ticker -> deque de precios
        self.volume_history = {}  # ticker -> deque de volúmenes
        self.spread_history = {}  # ticker -> deque de spreads
        
        self.max_history_days = 30
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Inicializa conexión con Rofex"""
        if not PYROFEX_AVAILABLE:
            logger.warning("pyRofex no disponible - modo simulación")
            self.connected = False
            return
        
        try:
            if self.environment == "remarket":
                rofex.initialize(user=self.user, 
                               password=self.password,
                               account=self.account, 
                               environment=rofex.Environment.REMARKET)
            else:
                rofex.initialize(user=self.user,
                               password=self.password,
                               account=self.account,
                               environment=rofex.Environment.LIVE)
            
            self.connected = True
            logger.info(f"✅ Conectado a Rofex ({self.environment})")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Rofex: {e}")
            self.connected = False
    
    def get_market_data(self, ticker: str, entries: List = None) -> Dict:
        """
        Obtiene market data actual de un ticker
        
        Args:
            ticker: Código del instrumento (ej: 'S17A6')
            entries: Lista de MarketDataEntry (default: LA, BI, OF, OI, TV)
        
        Returns:
            Dict con price, bid, offer, volume, etc.
        """
        if not self.connected or not PYROFEX_AVAILABLE:
            logger.warning("No conectado a Rofex, retornando datos simulados")
            return self._get_simulated_data(ticker)
        
        try:
            if entries is None:
                entries = [
                    rofex.MarketDataEntry.LAST,
                    rofex.MarketDataEntry.BIDS,
                    rofex.MarketDataEntry.OFFERS,
                    rofex.MarketDataEntry.VOLUME,
                    rofex.MarketDataEntry.OPEN_INTEREST
                ]
            
            data = rofex.get_market_data(ticker=ticker, entries=entries)
            
            # Parsear respuesta
            market_data = data.get('marketData', {})
            
            result = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'last_price': market_data.get('LA', {}).get('price'),
                'last_size': market_data.get('LA', {}).get('size'),
                'bid_price': market_data.get('BI', [{}])[0].get('price') if market_data.get('BI') else None,
                'bid_size': market_data.get('BI', [{}])[0].get('size') if market_data.get('BI') else None,
                'offer_price': market_data.get('OF', [{}])[0].get('price') if market_data.get('OF') else None,
                'offer_size': market_data.get('OF', [{}])[0].get('size') if market_data.get('OF') else None,
                'volume': market_data.get('TV'),
                'open_interest': market_data.get('OI'),
            }
            
            # Calcular spread
            if result['bid_price'] and result['offer_price']:
                mid = (result['bid_price'] + result['offer_price']) / 2
                result['spread_bps'] = ((result['offer_price'] - result['bid_price']) / mid) * 10000
            else:
                result['spread_bps'] = None
            
            # Actualizar históricos
            self._update_history(ticker, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo market data para {ticker}: {e}")
            return self._get_simulated_data(ticker)
    
    def get_historical_volume(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """
        Obtiene volumen histórico de un ticker
        
        Returns:
            DataFrame con columns: date, volume
        """
        if ticker in self.volume_history and len(self.volume_history[ticker]) > 0:
            # Usar cache
            return pd.DataFrame(list(self.volume_history[ticker]))
        
        # Si no hay cache, simular datos históricos
        logger.warning(f"No hay datos históricos para {ticker}, usando simulación")
        return self._simulate_historical_volume(ticker, days)
    
    def calculate_volume_metrics(self, ticker: str, window_days: int = 30) -> Dict:
        """
        Calcula métricas de volumen para detección de señales
        
        Returns:
            {
                'avg_volume_30d': float,
                'current_volume': float,
                'volume_pct_change': float,  # vs promedio
                'volume_trend': str  # 'increasing', 'decreasing', 'stable'
            }
        """
        hist = self.get_historical_volume(ticker, days=window_days)
        
        if hist.empty:
            return {
                'avg_volume_30d': 0,
                'current_volume': 0,
                'volume_pct_change': 0,
                'volume_trend': 'unknown'
            }
        
        current_data = self.get_market_data(ticker)
        current_volume = current_data.get('volume', 0) or 0
        
        avg_volume = hist['volume'].mean()
        pct_change = ((current_volume - avg_volume) / avg_volume) if avg_volume > 0 else 0
        
        # Detectar trend (últimos 5 días)
        recent_volumes = hist.tail(5)['volume'].values
        if len(recent_volumes) >= 3:
            trend_coef = np.polyfit(range(len(recent_volumes)), recent_volumes, 1)[0]
            if trend_coef > avg_volume * 0.05:
                trend = 'increasing'
            elif trend_coef < -avg_volume * 0.05:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'avg_volume_30d': avg_volume,
            'current_volume': current_volume,
            'volume_pct_change': pct_change,
            'volume_trend': trend
        }
    
    def calculate_spread_metrics(self, ticker: str, window_days: int = 30) -> Dict:
        """
        Calcula métricas de spread bid-offer
        
        Returns:
            {
                'current_spread_bps': float,
                'avg_spread_bps_30d': float,
                'spread_pct_increase': float,
                'spread_percentile': float  # percentil 0-100
            }
        """
        # Obtener spread actual
        current_data = self.get_market_data(ticker)
        current_spread = current_data.get('spread_bps', 0)
        
        # Histórico de spreads
        if ticker in self.spread_history and len(self.spread_history[ticker]) > 0:
            historical_spreads = [s for s in self.spread_history[ticker] if s is not None]
            
            if historical_spreads:
                avg_spread = np.mean(historical_spreads)
                spread_pct_increase = ((current_spread - avg_spread) / avg_spread) if avg_spread > 0 else 0
                
                # Calcular percentil
                percentile = (sum(s < current_spread for s in historical_spreads) / len(historical_spreads)) * 100
            else:
                avg_spread = current_spread
                spread_pct_increase = 0
                percentile = 50
        else:
            avg_spread = current_spread
            spread_pct_increase = 0
            percentile = 50
        
        return {
            'current_spread_bps': current_spread,
            'avg_spread_bps_30d': avg_spread,
            'spread_pct_increase': spread_pct_increase,
            'spread_percentile': percentile
        }
    
    def get_dollar_spread(self) -> Dict:
        """
        Obtiene spread MEP vs Oficial (señal de nerviosismo)
        
        Returns:
            {
                'mep': float,
                'oficial': float,
                'spread_pct': float,
                'timestamp': datetime
            }
        """
        # TODO: Implementar con datos reales de dólar
        # Por ahora simulado
        oficial = 1459.42  # Hardcoded ejemplo
        mep = oficial * 1.025  # 2.5% sobre oficial
        
        return {
            'mep': mep,
            'oficial': oficial,
            'spread_pct': (mep - oficial) / oficial,
            'timestamp': datetime.now()
        }
    
    def _update_history(self, ticker: str, data: Dict):
        """Actualiza históricos en cache"""
        # Inicializar deques si no existen
        if ticker not in self.price_history:
            self.price_history[ticker] = deque(maxlen=self.max_history_days)
            self.volume_history[ticker] = deque(maxlen=self.max_history_days)
            self.spread_history[ticker] = deque(maxlen=self.max_history_days)
        
        # Agregar datos
        self.price_history[ticker].append({
            'timestamp': data['timestamp'],
            'price': data['last_price']
        })
        
        self.volume_history[ticker].append({
            'timestamp': data['timestamp'],
            'volume': data['volume']
        })
        
        self.spread_history[ticker].append(data['spread_bps'])
    
    def _get_simulated_data(self, ticker: str) -> Dict:
        """Datos simulados cuando no hay conexión"""
        base_price = 100000  # ARS
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'last_price': base_price * (1 + np.random.uniform(-0.02, 0.02)),
            'last_size': int(np.random.uniform(100, 1000)),
            'bid_price': base_price * 0.998,
            'bid_size': int(np.random.uniform(500, 2000)),
            'offer_price': base_price * 1.002,
            'offer_size': int(np.random.uniform(500, 2000)),
            'volume': int(np.random.uniform(50000, 200000)),
            'open_interest': int(np.random.uniform(1000000, 5000000)),
            'spread_bps': 40 + np.random.uniform(-10, 10),
        }
    
    def _simulate_historical_volume(self, ticker: str, days: int) -> pd.DataFrame:
        """Simula volumen histórico para testing"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_volume = 150000
        
        volumes = []
        for i, date in enumerate(dates):
            # Simular trend decreciente hacia licitación
            days_to_event = days - i
            reduction_factor = 1 - (0.3 * (1 - days_to_event / days))
            
            volume = base_volume * reduction_factor * (1 + np.random.uniform(-0.15, 0.15))
            volumes.append(volume)
        
        return pd.DataFrame({
            'date': dates,
            'volume': volumes
        })


# ==================== TESTING ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Testing con datos simulados (sin credenciales reales)
    print("🔧 Testing Market Data Provider (modo simulado)\n")
    
    provider = MarketDataProvider(
        user="demo",
        password="demo",
        account="demo",
        environment="remarket"
    )
    
    ticker = "S17A6"
    
    # 1. Market data actual
    print(f"📊 Market Data para {ticker}:")
    data = provider.get_market_data(ticker)
    print(f"  Precio: ${data['last_price']:,.2f}")
    print(f"  Spread: {data['spread_bps']:.2f} bps")
    print(f"  Volumen: {data['volume']:,.0f}")
    print()
    
    # 2. Métricas de volumen
    print("📈 Métricas de Volumen:")
    vol_metrics = provider.calculate_volume_metrics(ticker, window_days=30)
    print(f"  Volumen promedio 30d: {vol_metrics['avg_volume_30d']:,.0f}")
    print(f"  Cambio vs promedio: {vol_metrics['volume_pct_change']:.1%}")
    print(f"  Trend: {vol_metrics['volume_trend']}")
    print()
    
    # 3. Métricas de spread
    print("📏 Métricas de Spread:")
    spread_metrics = provider.calculate_spread_metrics(ticker)
    print(f"  Spread actual: {spread_metrics['current_spread_bps']:.2f} bps")
    print(f"  Aumento vs promedio: {spread_metrics['spread_pct_increase']:.1%}")
    print(f"  Percentil: {spread_metrics['spread_percentile']:.0f}")
    print()
    
    # 4. Spread dólar
    print("💵 Spread MEP-Oficial:")
    dollar_spread = provider.get_dollar_spread()
    print(f"  MEP: ${dollar_spread['mep']:,.2f}")
    print(f"  Oficial: ${dollar_spread['oficial']:,.2f}")
    print(f"  Spread: {dollar_spread['spread_pct']:.2%}")
