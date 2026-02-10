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
├── src/                     # Código fuente
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── tesoro_scraper.py    # Scraper licitaciones
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── market_data.py       # Market data Rofex
│   │
│   ├── detector/
│   │   ├── __init__.py
│   │   └── signal_detector.py   # Generador de señales
│   │
│   ├── config.py            # Configuración centralizada
│   └── main.py              # Orquestador principal
│
├── tests/                   # Tests unitarios
├── logs/                    # Logs de ejecución
├── data_storage/            # Base de datos SQLite
│
├── quickstart.py            # Demo rápido
├── requirements.txt         # Dependencias
├── .env.example            # Template de credenciales
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar o descomprimir
cd licitacion_detector

# Crear virtualenv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Demo Rápido (sin credenciales)

```bash
# Ejecutar demo con datos simulados
python quickstart.py
```

**Output esperado:**
```
📅 Buscando licitaciones próximas...
✅ Encontradas 3 licitaciones próximas

📊 Obteniendo datos de mercado
  Precio: $102,450.50
  Volumen: 182,286
  Spread: 35.49 bps

🧠 Generando señales de trading
✅ Generadas 1 señales:
📉 SHORT S17A6 @ $102,450.00 | Confianza: 82.5%
  • Volumen cayó 32.4% vs promedio
  • Spread aumentó 18.2%
  • MEP spread 2.35%
```

### 3. Configuración para Trading Real

```bash
# Copiar template
cp .env.example .env

# Editar con tus credenciales
nano .env  # o tu editor favorito
```

**Obtener credenciales Rofex:**
- Demo (gratis): https://remarkets.primary.com.ar
- Producción: contactar mpi@primary.com.ar

### 4. Testing Paper Mode

```bash
# Un ciclo de detección (sin trades reales)
python src/main.py --mode paper --once

# Ver logs
tail -f logs/detector.log
```

### 5. Live Trading (Producción)

```bash
# IMPORTANTE: Solo después de 30+ días paper trading
python src/main.py --mode live
```

---

## 📈 Estrategia Implementada

### Pre-Licitación Trade

**Lógica:**
- **T-2/T-3 días:** Detectar señales (volumen ↓ 30%, spreads ↑ 15%)
- **Entry:** SHORT Lecaps cortas via repo
- **T+0 (15:01hs):** Resultados publicados
- **Exit:** Si rollover >95% → CLOSE con +2.5%

**ROI esperado:** 1.5-3% por trade (3 días holding)

**Configuración:**
```python
# Editar src/config.py
DETECTION_PARAMS = {
    'pre_licitacion_window': 3,      # días de análisis
    'volume_drop_threshold': 0.30,   # 30% caída volumen
    'spread_increase_threshold': 0.15, # 15% aumento spread
    'min_confidence_score': 0.75,    # Confianza mínima
}
```

---

## 🧪 Testing de Componentes

### Scraper de Licitaciones

```bash
cd src
python -m scrapers.tesoro_scraper
```

### Market Data Provider

```bash
cd src
python -m data.market_data
```

### Signal Detector

```bash
cd src
python -m detector.signal_detector
```

---

## 🔧 Configuración Avanzada

### Ajustar Umbrales

```python
# src/config.py

# Más conservador (menos trades, mayor confianza)
DETECTION_PARAMS = {
    'volume_drop_threshold': 0.40,  # 40% vs 30%
    'min_confidence_score': 0.85,   # 85% vs 75%
}

# Más agresivo (más trades, menor confianza)
DETECTION_PARAMS = {
    'volume_drop_threshold': 0.20,  # 20%
    'min_confidence_score': 0.65,   # 65%
}
```

### Risk Management

```python
# src/config.py
TRADING_PARAMS = {
    'position_size_pct': 0.15,      # 15% capital por trade
    'stop_loss_pct': 0.015,         # 1.5% stop loss
    'take_profit_pct': 0.025,       # 2.5% take profit
    'max_positions': 3,             # Máximo 3 posiciones
}
```

---

## 📊 Métricas & Monitoreo

### Logs

```bash
# Seguir logs en tiempo real
tail -f logs/detector.log

# Ver últimas señales generadas
grep "Señal generada" logs/detector.log | tail -20

# Ver PnL
grep "TARGET alcanzado\|STOP LOSS" logs/detector.log
```

### Base de Datos

```bash
# Acceder a SQLite
sqlite3 data_storage/licitaciones.db

# Ver últimas señales
SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10;

# PnL acumulado
SELECT SUM(pnl) FROM trades WHERE status='CLOSED';
```

---

## 🐛 Troubleshooting

### Error: "No conectado a Rofex"

**Solución:**
```bash
# 1. Verificar credenciales en .env
cat .env

# 2. Verificar que pyRofex está instalado
pip show pyRofex

# 3. Para testing, usar modo simulado (funciona sin credenciales)
python quickstart.py
```

### Error: "No hay datos históricos"

**Causa:** Primera ejecución, cache vacío

**Solución:**
- El sistema acumulará datos automáticamente en 7-14 días
- Mientras tanto, funciona con datos simulados

### Señales con baja confianza

**Solución:**
```python
# Reducir threshold en src/config.py
DETECTION_PARAMS = {
    'min_confidence_score': 0.65,  # de 0.75 a 0.65
}
```

---

## 🚀 Roadmap

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
- Teramot: [teramot.ai](https://teramot.ai)

---

## 📄 Licencia

MIT License - Ver `LICENSE` para detalles

---

**Built with ❤️ in Argentina 🇦🇷**
