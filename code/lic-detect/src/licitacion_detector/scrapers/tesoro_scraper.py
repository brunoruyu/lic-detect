"""
Scraper de licitaciones del Tesoro Nacional argentino
Extrae fechas, instrumentos y montos de las licitaciones programadas
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TesoritacionScraper:
    """Scraper para extraer info de licitaciones del Tesoro"""
    
    def __init__(self):
        self.base_url = "https://www.argentina.gob.ar"
        self.licitaciones_url = f"{self.base_url}/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_next_licitaciones(self, days_ahead: int = 30) -> List[Dict]:
        """
        Obtiene las próximas licitaciones programadas
        
        Returns:
            Lista de dicts con: fecha, instrumentos, vencimientos_ars, url
        """
        try:
            logger.info(f"Scrapeando licitaciones desde {self.licitaciones_url}")
            response = self.session.get(self.licitaciones_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            licitaciones = []
            
            # Buscar llamados a licitación recientes
            articles = soup.find_all('article', class_='node-noticia')
            
            for article in articles[:10]:  # Top 10 más recientes
                try:
                    lic_data = self._parse_licitacion_article(article)
                    if lic_data and self._is_upcoming(lic_data['fecha'], days_ahead):
                        licitaciones.append(lic_data)
                except Exception as e:
                    logger.warning(f"Error parseando artículo: {e}")
                    continue
            
            logger.info(f"Encontradas {len(licitaciones)} licitaciones próximas")
            return sorted(licitaciones, key=lambda x: x['fecha'])
            
        except Exception as e:
            logger.error(f"Error scrapeando licitaciones: {e}")
            return []
    
    def _parse_licitacion_article(self, article) -> Optional[Dict]:
        """Parsea un artículo de licitación"""
        try:
            # Extraer título y link
            title_tag = article.find('h3') or article.find('h2')
            if not title_tag:
                return None
            
            title = title_tag.get_text(strip=True)
            
            # Verificar que sea una licitación
            if not any(word in title.lower() for word in ['licitación', 'licitacion', 'llamado']):
                return None
            
            # Extraer link
            link_tag = title_tag.find('a') or article.find('a')
            link = self.base_url + link_tag['href'] if link_tag else None
            
            # Extraer fecha del título o contenido
            fecha = self._extract_fecha(title)
            if not fecha:
                # Intentar extraer del cuerpo
                body = article.get_text()
                fecha = self._extract_fecha(body)
            
            if not fecha:
                return None
            
            # Extraer instrumentos mencionados
            instrumentos = self._extract_instrumentos(title + " " + article.get_text())
            
            return {
                'fecha': fecha,
                'titulo': title,
                'instrumentos': instrumentos,
                'url': link,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error en _parse_licitacion_article: {e}")
            return None
    
    def _extract_fecha(self, text: str) -> Optional[datetime]:
        """
        Extrae fecha de un texto
        Formatos: "14 de enero", "miércoles 14 de enero", etc.
        """
        # Mapeo de meses
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Patrón: "14 de enero de 2026" o "14 de enero"
        pattern = r'(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?'
        match = re.search(pattern, text.lower())
        
        if match:
            dia = int(match.group(1))
            mes_str = match.group(2)
            año = int(match.group(3)) if match.group(3) else datetime.now().year
            
            if mes_str in meses:
                mes = meses[mes_str]
                try:
                    return datetime(año, mes, dia)
                except ValueError:
                    pass
        
        # Patrón alternativo: "2026-01-14"
        pattern2 = r'(\d{4})-(\d{2})-(\d{2})'
        match2 = re.search(pattern2, text)
        if match2:
            try:
                return datetime(int(match2.group(1)), int(match2.group(2)), int(match2.group(3)))
            except ValueError:
                pass
        
        return None
    
    def _extract_instrumentos(self, text: str) -> List[str]:
        """Extrae códigos de instrumentos del texto"""
        instrumentos = []
        
        # Patrones comunes: S17A6, TZX26, D30A6, etc.
        patterns = [
            r'[STXMD]\d{1,2}[A-Z]\d',  # S17A6, T30J6
            r'[STXMD]\d{1,2}[A-Z]\d{2}',  # TZX26
            r'TZX[D]?\d{1,2}',  # TZXD6
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            instrumentos.extend(matches)
        
        return list(set(instrumentos))  # Únicos
    
    def _is_upcoming(self, fecha: datetime, days_ahead: int) -> bool:
        """Verifica si la fecha está dentro de los próximos N días"""
        now = datetime.now()
        cutoff = now + timedelta(days=days_ahead)
        return now <= fecha <= cutoff
    
    def get_licitacion_details(self, url: str) -> Dict:
        """
        Obtiene detalles completos de una licitación específica
        (instrumentos, montos, horarios)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer texto completo
            content = soup.find('div', class_='node-body') or soup.find('article')
            if not content:
                return {}
            
            text = content.get_text()
            
            # Extraer información clave
            details = {
                'instrumentos': self._extract_instrumentos(text),
                'horario_inicio': self._extract_horario(text, 'inicio'),
                'horario_cierre': self._extract_horario(text, 'cierre'),
                'vencimientos': self._extract_vencimientos(text),
                'full_text': text[:1000]  # Primeros 1000 chars
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de {url}: {e}")
            return {}
    
    def _extract_horario(self, text: str, tipo: str) -> Optional[str]:
        """Extrae horario de inicio o cierre"""
        # Patrón: "10:00 horas" o "15:00"
        keywords = {
            'inicio': ['comenzará', 'iniciará', 'apertura'],
            'cierre': ['finalizará', 'cierre', 'hasta']
        }
        
        for keyword in keywords.get(tipo, []):
            pattern = rf'{keyword}[^0-9]*(\d{{1,2}}:\d{{2}})'
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_vencimientos(self, text: str) -> Optional[float]:
        """Extrae monto de vencimientos en billones de ARS"""
        # Patrón: "$9,6 billones" o "9.6 billones"
        pattern = r'[\$\s]*([\d,\.]+)\s*billones'
        match = re.search(pattern, text.lower())
        
        if match:
            try:
                monto_str = match.group(1).replace(',', '.')
                return float(monto_str)
            except ValueError:
                pass
        
        return None


# ==================== TESTING ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = TesoritacionScraper()
    
    print("🔍 Buscando licitaciones próximas...")
    lics = scraper.get_next_licitaciones(days_ahead=45)
    
    print(f"\n📅 Encontradas {len(lics)} licitaciones:\n")
    for lic in lics:
        print(f"Fecha: {lic['fecha'].strftime('%Y-%m-%d')}")
        print(f"Título: {lic['titulo']}")
        print(f"Instrumentos: {', '.join(lic['instrumentos']) if lic['instrumentos'] else 'N/A'}")
        print(f"URL: {lic['url']}")
        print("-" * 80)
        
        # Obtener detalles si hay URL
        if lic['url']:
            print("\n📋 Obteniendo detalles...")
            details = scraper.get_licitacion_details(lic['url'])
            if details:
                print(f"  Horario: {details.get('horario_inicio', 'N/A')} - {details.get('horario_cierre', 'N/A')}")
                print(f"  Vencimientos: ${details.get('vencimientos', 'N/A')} billones")
            print("=" * 80)
            print()
