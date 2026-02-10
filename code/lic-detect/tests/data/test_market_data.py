"""
Tests para MarketDataProvider
"""
import pytest
from datetime import datetime
from licitacion_detector.data.market_data import MarketDataProvider


class TestMarketDataProvider:
    """Tests para el provider de market data"""
    
    def setup_method(self):
        """Setup antes de cada test - usa modo simulado"""
        self.provider = MarketDataProvider(
            user="test",
            password="test",
            account="test",
            environment="remarket"
        )
    
    def test_initialization(self):
        """Test que el provider se inicializa correctamente"""
        assert self.provider is not None
        assert self.provider.user == "test"
        assert self.provider.max_history_days == 30
    
    def test_get_simulated_data(self):
        """Test datos simulados"""
        ticker = "S17A6"
        data = self.provider._get_simulated_data(ticker)
        
        assert data is not None
        assert data['ticker'] == ticker
        assert 'last_price' in data
        assert 'volume' in data
        assert 'spread_bps' in data
        assert data['last_price'] > 0
        assert data['volume'] > 0
    
    def test_get_market_data_simulated(self):
        """Test obtención de market data (simulado)"""
        ticker = "S17A6"
        data = self.provider.get_market_data(ticker)
        
        assert data is not None
        assert data['ticker'] == ticker
        assert isinstance(data['timestamp'], datetime)
        assert data['last_price'] > 0
    
    def test_calculate_volume_metrics(self):
        """Test cálculo de métricas de volumen"""
        ticker = "TZX26"
        
        # Obtener datos primero para poblar histórico
        self.provider.get_market_data(ticker)
        
        metrics = self.provider.calculate_volume_metrics(ticker)
        
        assert metrics is not None
        assert 'avg_volume_30d' in metrics
        assert 'current_volume' in metrics
        assert 'volume_pct_change' in metrics
        assert 'volume_trend' in metrics
    
    def test_calculate_spread_metrics(self):
        """Test cálculo de métricas de spread"""
        ticker = "S31L6"
        
        # Obtener datos primero
        self.provider.get_market_data(ticker)
        
        metrics = self.provider.calculate_spread_metrics(ticker)
        
        assert metrics is not None
        assert 'current_spread_bps' in metrics
        assert 'avg_spread_bps_30d' in metrics
        assert 'spread_pct_increase' in metrics
        assert 'spread_percentile' in metrics
    
    def test_get_dollar_spread(self):
        """Test obtención de spread MEP-oficial"""
        spread_data = self.provider.get_dollar_spread()
        
        assert spread_data is not None
        assert 'mep' in spread_data
        assert 'oficial' in spread_data
        assert 'spread_pct' in spread_data
        assert spread_data['mep'] > 0
        assert spread_data['oficial'] > 0
    
    def test_update_history(self):
        """Test actualización de históricos"""
        ticker = "D30A6"
        
        # Simular datos
        data = {
            'timestamp': datetime.now(),
            'last_price': 100000,
            'volume': 50000,
            'spread_bps': 40
        }
        
        # Actualizar histórico
        self.provider._update_history(ticker, data)
        
        # Verificar que se crearon las estructuras
        assert ticker in self.provider.price_history
        assert ticker in self.provider.volume_history
        assert ticker in self.provider.spread_history
        
        # Verificar que tienen datos
        assert len(self.provider.price_history[ticker]) > 0
        assert len(self.provider.volume_history[ticker]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
