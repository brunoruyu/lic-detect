"""
Tests para TesoritacionScraper
"""
import pytest
from datetime import datetime, timedelta
from licitacion_detector.scrapers.tesoro_scraper import TesoritacionScraper


class TestTesoritacionScraper:
    """Tests para el scraper de licitaciones"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.scraper = TesoritacionScraper()
    
    def test_initialization(self):
        """Test que el scraper se inicializa correctamente"""
        assert self.scraper is not None
        assert self.scraper.base_url == "https://www.argentina.gob.ar"
        assert self.scraper.session is not None
    
    def test_extract_fecha_formato_completo(self):
        """Test extracción de fecha en formato completo"""
        text = "La licitación será el 14 de febrero de 2026"
        fecha = self.scraper._extract_fecha(text)
        
        assert fecha is not None
        assert fecha.day == 14
        assert fecha.month == 2
        assert fecha.year == 2026
    
    def test_extract_fecha_sin_año(self):
        """Test extracción de fecha sin año (asume año actual)"""
        text = "Llamado para el 28 de marzo"
        fecha = self.scraper._extract_fecha(text)
        
        assert fecha is not None
        assert fecha.day == 28
        assert fecha.month == 3
    
    def test_extract_instrumentos(self):
        """Test extracción de códigos de instrumentos"""
        text = "Se licitan los siguientes instrumentos: S17A6, TZX26, D30A6"
        instrumentos = self.scraper._extract_instrumentos(text)
        
        assert len(instrumentos) >= 3
        assert "S17A6" in instrumentos
        assert "TZX26" in instrumentos
        assert "D30A6" in instrumentos
    
    def test_is_upcoming(self):
        """Test verificación de fecha próxima"""
        # Fecha futura dentro de ventana
        fecha_futura = datetime.now() + timedelta(days=10)
        assert self.scraper._is_upcoming(fecha_futura, days_ahead=30) is True
        
        # Fecha muy lejana
        fecha_lejana = datetime.now() + timedelta(days=50)
        assert self.scraper._is_upcoming(fecha_lejana, days_ahead=30) is False
        
        # Fecha pasada
        fecha_pasada = datetime.now() - timedelta(days=5)
        assert self.scraper._is_upcoming(fecha_pasada, days_ahead=30) is False
    
    def test_extract_vencimientos(self):
        """Test extracción de montos de vencimientos"""
        text = "Los vencimientos ascienden a $12.5 billones"
        vencimiento = self.scraper._extract_vencimientos(text)
        
        assert vencimiento is not None
        assert vencimiento == 12.5
    
    @pytest.mark.skip(reason="Requiere conexión a internet")
    def test_get_next_licitaciones_integration(self):
        """Test de integración - requiere internet"""
        licitaciones = self.scraper.get_next_licitaciones(days_ahead=30)
        # Puede retornar lista vacía si no hay licitaciones o si el scraping falla
        assert isinstance(licitaciones, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
