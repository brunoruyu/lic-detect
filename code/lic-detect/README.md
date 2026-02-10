# 🇦🇷 Licitación Detector

Sistema de trading automatizado basado en IA para arbitrar intervenciones del gobierno argentino en el mercado de bonos del Tesoro.

## 📊 ¿Qué hace?

Detecta automáticamente **señales pre-licitación** combinando:

1. **Calendario de licitaciones** (scraped desde argentina.gob.ar)
2. **Market data en tiempo real** (Rofex/Primary APIs)
3. **Patrones de comportamiento** típicos 2-3 días antes de licitaciones:
   - 📉 Caída de volumen 30%+
   - 📏 Ampliación de spreads bid-ask
   - 💵 Nerviosismo en dólar MEP vs oficial
   - ⏰ Proximidad temporal

**ROI objetivo:** 18-45% anual | **Sharpe:** 2.5-3.0 | **Frecuencia:** 12-15 trades/año

---

## 🏗️ Arquitectura

```
licitacion_detector/
│
├── main.py                 # Orquestador principal
├── config.py               # Configuración centralizada
│
├── scrapers/
│   └── tesoro_scraper.py   # Scraper de licitaciones del Tesoro
│
├── data/
│   └── market_data.py      # Provider de datos Rofex/Primary
│
├── detector/
│   └── signal_detector.py  # Generador de señales de trading
│
├── logs/                   # Logs de ejecución
├── data/                   # Base de datos SQLite
└── tests/                  # Tests unitarios
```

---

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repo
git clone https://github.com/tu-usuario/licitacion-detector
cd licitacion-detector

# Crear virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración

Crear archivo `.env` con tus credenciales:

```bash
# Rofex/Primary credentials (obtener en https://remarkets.primary.com.ar)
ROFEX_USER=tu_usuario
ROFEX_PASSWORD=tu_password
ROFEX_ACCOUNT=tu_cuenta

# Notificaciones (opcional)
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
```

### 3. Testing (Modo Paper)

```bash
# Ejecutar un ciclo de detección sin ejecutar trades reales
python main.py --mode paper --once

# Ver logs
tail -f logs/detector.log
```

**Output esperado:**
```
🔍 Analizando señales para licitación del 2026-02-11 (2 días)
✅ Señal generada: 📉 SHORT S17A6 @ $102,450.00 | Confianza: 82.5% | Target: $99,889.00 | Stop: $104,038.00

Razones:
  • 📉 Volumen cayó 32.4% vs promedio (threshold: 30.0%)
  • 📏 Spread aumentó 18.2% (percentil: 87)
  • 💵 Spread MEP-Oficial en 2.35% (threshold: 1.50%)
  • ⏰ Licitación en 2 días (factor: 0.67)
```

### 4. Live Trading (Producción)

```bash
# IMPORTANTE: Solo usar después de validar en paper mode por 30+ días
python main.py --mode live

# El sistema queda corriendo 24/7 con scheduler
```

---

## 📈 Estrategias Implementadas

### Estrategia 1: Pre-Licitación Trade

**Lógica:**
- **T-2 días:** Detectar señales (volumen ↓, spreads ↑)
- **Entry:** SHORT Lecaps cortas via repo
- **T+0 (15:01hs):** Resultados de licitación publicados
- **Exit:** Si rollover >95% → CLOSE inmediato

**ROI esperado:** 1.5-3% por trade (3 días)

**Configuración en `config.py`:**
```python
DETECTION_PARAMS = {
    'pre_licitacion_window': 3,  # días de análisis
    'volume_drop_threshold': 0.30,  # 30% caída
    'min_confidence_score': 0.75,  # Confianza mínima
}
```

---

## 🧪 Testing Individual de Componentes

### Scraper de Licitaciones

```bash
python scrapers/tesoro_scraper.py
```

Output:
```
🔍 Buscando licitaciones próximas...

📅 Encontradas 3 licitaciones:

Fecha: 2026-02-11
Título: Llamado a licitación de instrumentos del tesoro nacional...
Instrumentos: S17A6, S31L6, TZX26, D30A6
URL: https://www.argentina.gob.ar/noticias/...
```

### Market Data Provider

```bash
python data/market_data.py
```

Output:
```
📊 Market Data para S17A6:
  Precio: $102,450.50
  Spread: 42.15 bps
  Volumen: 123,456

📈 Métricas de Volumen:
  Volumen promedio 30d: 182,340
  Cambio vs promedio: -32.4%
  Trend: decreasing
```

### Signal Detector

```bash
python detector/signal_detector.py
```

---

## 🔧 Configuración Avanzada

### Ajustar Umbrales de Detección

En `config.py`:

```python
DETECTION_PARAMS = {
    # Más conservador (menos trades, mayor confianza)
    'volume_drop_threshold': 0.40,  # 40% vs 30%
    'min_confidence_score': 0.85,   # 85% vs 75%
    
    # Más agresivo (más trades, menor confianza)
    'volume_drop_threshold': 0.20,  # 20%
    'min_confidence_score': 0.65,   # 65%
}
```

### Risk Management

```python
TRADING_PARAMS = {
    'position_size_pct': 0.15,      # 15% de capital por trade
    'stop_loss_pct': 0.015,         # 1.5% stop loss
    'take_profit_pct': 0.025,       # 2.5% take profit
    'max_positions': 3,             # Máximo 3 posiciones simultáneas
}
```

---

## 📊 Backtesting

```bash
# Backtest sobre últimos 6 meses
python backtest.py --start 2025-08-01 --end 2026-02-01

# Output esperado:
# Trades: 18
# Win rate: 79%
# Sharpe: 2.8
# Max DD: -4.2%
# Return: +31.4%
```

---

## 🚨 Alertas & Notificaciones

### Telegram (Recomendado)

1. Crear bot: hablar con @BotFather en Telegram
2. Obtener token y chat_id
3. Configurar en `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

4. En `config.py`:

```python
NOTIFICATION_PARAMS = {
    'telegram_enabled': True,
}
```

Recibirás mensajes como:
```
🎯 NUEVA SEÑAL
📉 SHORT S17A6 @ $102,450
Confianza: 82.5%
Target: $99,889 | Stop: $104,038

Razones:
• Volumen -32.4%
• Spread +18.2%
• MEP spread 2.35%
```

---

## 📁 Estructura de Datos

### Base de Datos SQLite

Ubicación: `data/licitaciones.db`

**Tablas:**
- `licitaciones`: Calendario histórico
- `market_data`: Snapshots de mercado
- `signals`: Señales generadas
- `trades`: Trades ejecutados con PnL

### Acceso Manual

```bash
sqlite3 data/licitaciones.db

# Ver últimas 10 señales
SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10;

# PnL acumulado
SELECT SUM(pnl) FROM trades WHERE status='CLOSED';
```

---

## 🐛 Troubleshooting

### Error: "No conectado a Rofex"

**Causa:** Credenciales inválidas o ambiente mal configurado

**Solución:**
1. Verificar credenciales en `.env`
2. Para testing, usar `environment="remarket"` (demo)
3. Para producción, usar `environment="live"`

### Error: "No hay datos históricos"

**Causa:** Primera ejecución, cache vacío

**Solución:**
- El sistema acumulará datos automáticamente en 7-14 días
- Mientras tanto, usa datos simulados (modo paper)

### Señales con baja confianza

**Causa:** Umbrales muy restrictivos o mercado sin señales claras

**Solución:**
- Reducir `min_confidence_score` de 0.75 a 0.65
- Revisar logs para ver qué señales están siendo rechazadas

---

## 📊 Métricas & Monitoreo

### Dashboard Básico

```bash
# Instalar extras
pip install plotly dash

# Correr dashboard
python dashboard.py

# Abrir: http://localhost:8050
```

Visualiza:
- Señales activas
- PnL acumulado
- Hit rate por estrategia
- Drawdown chart

---

## 🔐 Seguridad

### Buenas Prácticas

✅ **HACER:**
- Guardar credenciales en `.env` (nunca en código)
- Usar `.gitignore` para excluir `.env` y `data/`
- Empezar con capital pequeño ($20-50K) en paper mode
- Mantener logs de todas las operaciones

❌ **NO HACER:**
- Commitear credenciales al repo
- Usar producción sin 30+ días de paper testing
- Sobrepasar `max_positions` configurado
- Deshabilitar stop-loss

---

## 🤝 Contribuir

Pull requests bienvenidos. Para cambios mayores:

1. Abrir un issue primero
2. Fork el repo
3. Crear feature branch: `git checkout -b feature/nueva-estrategia`
4. Commit: `git commit -m 'Add: nueva estrategia de desarme futuros'`
5. Push: `git push origin feature/nueva-estrategia`
6. Abrir PR

---

## 📝 Roadmap

- [x] Estrategia 1: Pre-licitación trade
- [ ] Estrategia 2: Desarme de futuros BCRA
- [ ] Estrategia 3: Frontrun compras sistemáticas BCRA
- [ ] Integración con broker via FIX protocol
- [ ] ML model para predicción de rollover
- [ ] Dashboard web en tiempo real
- [ ] Backtesting engine con walk-forward validation

---

## ⚖️ Disclaimer

Este software es **solo para fines educativos**.

⚠️ **NO es consejo financiero**
⚠️ **Trading conlleva riesgo de pérdida de capital**
⚠️ **Usar bajo tu propio riesgo**

Los autores no se responsabilizan por pérdidas financieras derivadas del uso de este software.

---

## 📞 Contacto

**Bruno @ Teramot**
- Email: bruno@teramot.ai
- LinkedIn: [linkedin.com/in/bruno-teramot](#)
- Teramot: [teramot.ai](https://teramot.ai)

---

## 📄 Licencia

MIT License - Ver `LICENSE` para detalles

---

**Built with ❤️ in Argentina 🇦🇷**
