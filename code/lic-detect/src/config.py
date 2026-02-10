"""
Configuración central del Licitación Detector
"""
from datetime import datetime
import os

# ==================== API KEYS ====================
# TODO: Mover a variables de entorno en producción
ROFEX_USER = os.getenv("ROFEX_USER", "your_user")
ROFEX_PASSWORD = os.getenv("ROFEX_PASSWORD", "your_pass")
ROFEX_ACCOUNT = os.getenv("ROFEX_ACCOUNT", "your_account")

# URLs base
ROFEX_BASE_URL = "https://api.remarkets.primary.com.ar"
TESORO_LICITACIONES_URL = "https://www.argentina.gob.ar/economia/finanzas/licitaciones-de-letras-y-bonos-del-tesoro"
BCRA_IPOM_URL = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_de_politica_monetaria.asp"

# ==================== ESTRATEGIA ====================
# Parámetros de detección de señales pre-licitación

DETECTION_PARAMS = {
    # Ventana de análisis pre-licitación (días)
    "pre_licitacion_window": 3,
    
    # Umbrales de señales
    "volume_drop_threshold": 0.30,  # 30% caída en volumen
    "spread_increase_threshold": 0.15,  # 15% aumento en spread
    "mep_oficial_threshold": 0.015,  # 1.5% spread MEP-oficial
    
    # Confianza mínima para trade (0-1)
    "min_confidence_score": 0.75,
    
    # Instrumentos a monitorear
    "instrumentos_lecap": ["S17A6", "S31L6", "S30N6", "T15E7"],
    "instrumentos_cer": ["TZX26", "TZXD6", "TZX27", "TZX28"],
    "instrumentos_linked": ["D30A6"],
    
    # Horarios de operación (UTC-3 Argentina)
    "market_open": "11:00",
    "market_close": "18:00",
}

# ==================== TRADING ====================
TRADING_PARAMS = {
    # Tamaño de posición inicial
    "initial_capital_usd": 50000,
    "position_size_pct": 0.15,  # 15% por trade
    
    # Risk management
    "stop_loss_pct": 0.015,  # 1.5% stop loss
    "take_profit_pct": 0.025,  # 2.5% take profit
    "max_positions": 3,
    
    # Costos
    "commission_pct": 0.001,  # 0.1% comisiones
    "slippage_pct": 0.0015,  # 0.15% slippage estimado
}

# ==================== NOTIFICACIONES ====================
NOTIFICATION_PARAMS = {
    "telegram_enabled": False,
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    
    "email_enabled": False,
    "email_from": os.getenv("EMAIL_FROM", ""),
    "email_to": os.getenv("EMAIL_TO", ""),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": 587,
}

# ==================== LOGGING ====================
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/detector.log",
    "max_bytes": 10485760,  # 10MB
    "backup_count": 5,
}

# ==================== DATABASE ====================
DB_CONFIG = {
    "path": "data_storage/licitaciones.db",
    "backup_enabled": True,
    "backup_frequency_hours": 24,
}

# ==================== FECHAS IMPORTANTES ====================
# Hardcoded para arrancar - luego se scrapean automáticamente
LICITACIONES_2026 = [
    {"fecha": "2026-01-14", "vencimientos_ars": 9.6},  # billones
    {"fecha": "2026-01-28", "vencimientos_ars": 12.3},
    {"fecha": "2026-02-11", "vencimientos_ars": 10.8},
    {"fecha": "2026-02-25", "vencimientos_ars": 15.2},
    # Se irán agregando dinámicamente
]

# ==================== HELPERS ====================
def get_current_timestamp():
    """Retorna timestamp actual en formato ISO"""
    return datetime.now().isoformat()

def is_market_hours():
    """Verifica si estamos en horario de mercado"""
    now = datetime.now()
    market_open = datetime.strptime(DETECTION_PARAMS["market_open"], "%H:%M").time()
    market_close = datetime.strptime(DETECTION_PARAMS["market_close"], "%H:%M").time()
    
    # Verifica día hábil (lunes a viernes)
    if now.weekday() >= 5:
        return False
    
    return market_open <= now.time() <= market_close

def get_next_licitacion():
    """Retorna la próxima licitación programada"""
    now = datetime.now()
    for lic in LICITACIONES_2026:
        lic_date = datetime.strptime(lic["fecha"], "%Y-%m-%d")
        if lic_date > now:
            return lic
    return None
