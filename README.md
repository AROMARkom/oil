# WTI Oil Trading Bot

Systematyczny bot tradingowy do handlu ropą WTI (CFD) oparty na strategii volatility expansion i strukturalnego wybicia.

## 🎯 Opis

Bot analizuje rynek WTI Crude Oil na interwale M15, identyfikuje kompresję zmienności, filtruje sesje handlowe (London/NY), zarządza ryzykiem w oparciu o ATR oraz realizuje częściowe take profit. Logika decyzyjna działa w Pythonie, a egzekucja zleceń odbywa się przez MetaTrader 5 jako warstwę wykonawczą.

## ✨ Główne funkcje

### Strategia Trading
- **Volatility Expansion Detection**: Identyfikacja kompresji i ekspansji zmienności
- **Structural Breakout**: Detekcja wybić powyżej oporu i poniżej wsparcia
- **M15 Timeframe**: Analiza na 15-minutowych świecach
- **Momentum Confirmation**: Potwierdzenie kierunku trendu

### Zarządzanie Ryzykiem
- **ATR-based Position Sizing**: Dynamiczne określanie wielkości pozycji
- **Stop Loss**: 2.0x ATR jako domyślne SL
- **Max Risk per Trade**: 2% kapitału na transakcję
- **Daily Drawdown Control**: Maksymalny dzienny drawdown 5%
- **Total Drawdown Control**: Maksymalny całkowity drawdown 15%

### Take Profit i Trailing Stop
- **Partial Take Profit**: Częściowe zamykanie pozycji na poziomach:
  - 50% pozycji na 2.0x ATR
  - 30% pozycji na 3.5x ATR
  - 20% pozycji na 5.0x ATR
- **Trailing Stop**: Aktywacja po 2.5x ATR zysku, trail na 1.5x ATR

### Filtrowanie
- **Session Filter**: Handel tylko w sesjach London (8-16 UTC) i NY (13-21 UTC)
- **News Avoidance**: Automatyczne unikanie EIA Petroleum Status Report (Środa 15:30 UTC)
- **Risk Controls**: Wbudowane mechanizmy kontroli drawdownu

## 📋 Wymagania

- Python 3.8+
- MetaTrader 5
- Konto z brokerem wspierającym MT5 i CFD na WTI

## 🚀 Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/AROMARkom/oil.git
cd oil
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Zainstaluj i skonfiguruj MetaTrader 5:
   - Pobierz MT5 ze strony swojego brokera
   - Zaloguj się na konto
   - Upewnij się, że MT5 jest uruchomiony podczas działania bota

## ⚙️ Konfiguracja

Edytuj plik `config/config.yaml` aby dostosować parametry bota:

```yaml
# Przykładowa konfiguracja
symbol: "WTI"
timeframe: "M15"

risk:
  max_risk_per_trade: 0.02  # 2%
  max_daily_drawdown: 0.05   # 5%
  
sessions:
  london:
    enabled: true
  newyork:
    enabled: true
```

## 🎮 Użycie

### Podstawowe uruchomienie

```python
from src.trading_bot import WTIOilTradingBot

# Utwórz instancję bota
bot = WTIOilTradingBot()

# Połącz z MT5
if bot.connect_mt5():
    # Uruchom bota (sprawdzanie co 60 sekund)
    bot.run(check_interval=60)
```

### Uruchomienie z wiersza poleceń

```bash
python -m src.trading_bot
```

### Zatrzymanie bota

Naciśnij `Ctrl+C` aby bezpiecznie zatrzymać bota.

## 📊 Struktura projektu

```
oil/
├── src/
│   ├── core/
│   │   └── config.py              # Zarządzanie konfiguracją
│   ├── strategies/
│   │   └── volatility_expansion.py # Strategia volatility expansion
│   ├── indicators/
│   │   ├── volatility.py          # Wskaźniki zmienności (ATR)
│   │   └── breakout.py            # Detekcja wybić
│   ├── risk/
│   │   ├── risk_manager.py        # Zarządzanie ryzykiem
│   │   └── profit_manager.py      # Zarządzanie zyskiem
│   ├── execution/
│   │   └── mt5_connector.py       # Integracja z MT5
│   ├── utils/
│   │   ├── session_filter.py      # Filtrowanie sesji
│   │   ├── news_calendar.py       # Kalendarz newsów
│   │   └── logger.py              # System logowania
│   └── trading_bot.py             # Główny orchestrator
├── config/
│   └── config.yaml                # Konfiguracja bota
├── tests/                         # Testy jednostkowe
├── logs/                          # Logi (tworzone automatycznie)
├── requirements.txt               # Zależności Python
└── README.md                      # Ta dokumentacja
```

## 🔍 Jak działa strategia?

### 1. Detekcja kompresji zmienności
Bot monitoruje ATR (Average True Range) i identyfikuje okresy, gdy zmienność spada poniżej progu (60% średniej z 20 okresów).

### 2. Czekanie na ekspansję
Po kompresji bot czeka na wzrost zmienności (1.5x poprzedniej wartości ATR).

### 3. Identyfikacja struktury rynku
Bot określa poziomy wsparcia i oporu na podstawie 10 ostatnich świec.

### 4. Potwierdzenie wybicia
Generowany jest sygnał gdy:
- Następuje ekspansja zmienności
- Cena wybija powyżej oporu (BUY) lub poniżej wsparcia (SELL)
- Momentum potwierdza kierunek
- Wielkość wybicia przekracza 0.3x ATR

### 5. Zarządzanie pozycją
- Stop Loss: 2.0x ATR od ceny wejścia
- Częściowe TP: 3 poziomy (50%, 30%, 20%)
- Trailing Stop: Aktywacja po 2.5x ATR zysku

## 📈 Filtrowanie i kontrola ryzyka

### Sesje handlowe
- **London**: 8:00 - 16:00 UTC (najbardziej płynna dla ropy)
- **New York**: 13:00 - 21:00 UTC (pokrywa otwarcie USA)
- **Overlap**: 13:00 - 16:00 UTC (najlepsza płynność)

### Unikanie newsów
Bot automatycznie unika handlu podczas:
- **EIA Petroleum Status Report**: Środa 15:30 UTC (±30/60 min)
- Można dodać inne wydarzenia w `news_calendar.py`

### Kontrola Drawdownu
- Dzienny limit: 5% od balansu na początek dnia
- Całkowity limit: 15% od peak equity
- Automatyczne zatrzymanie handlu po przekroczeniu limitów

## 🧪 Testowanie

```bash
# Uruchom testy jednostkowe
pytest tests/

# Z pokryciem kodu
pytest --cov=src tests/
```

## 📝 Logowanie

Bot tworzy szczegółowe logi w katalogu `logs/`:
- Wszystkie sygnały handlowe
- Otwarcie/zamknięcie pozycji
- Status filtrów (sesja, news, ryzyko)
- Statystyki (co godzinę)

## ⚠️ Ostrzeżenia

- **Trading wiąże się z ryzykiem**: Ten bot jest narzędziem automatycznym i może generować straty
- **Testuj na demo**: Zawsze testuj strategię na koncie demo przed użyciem na koncie rzeczywistym
- **Monitoruj bota**: Regularnie sprawdzaj działanie i logi
- **Backup**: Zachowaj backup konfiguracji i danych
- **Broker**: Upewnij się, że Twój broker wspiera API MT5

## 🔧 Customizacja

### Zmiana parametrów strategii
Edytuj `config/config.yaml`:
```yaml
strategy:
  volatility:
    compression_period: 20
    compression_threshold: 0.6
    expansion_multiplier: 1.5
```

### Dodanie nowych filtrów
Rozszerz `check_filters()` w `trading_bot.py`.

### Modyfikacja logiki Take Profit
Edytuj poziomy w konfiguracji:
```yaml
take_profit:
  levels:
    - target_atr_multiple: 2.0
      close_percentage: 0.5
```

## 📞 Wsparcie

W przypadku pytań lub problemów:
1. Sprawdź logi w `logs/trading_bot.log`
2. Przejrzyj konfigurację w `config/config.yaml`
3. Otwórz issue na GitHubie

## 📄 Licencja

MIT License - zobacz plik LICENSE

## 🙏 Podziękowania

Bot wykorzystuje:
- MetaTrader 5 API
- NumPy do obliczeń numerycznych
- PyYAML do zarządzania konfiguracją

---

**Disclaimer**: Ten software jest dostarczany "as is" bez żadnych gwarancji. Użytkowanie na własne ryzyko. Zawsze testuj na koncie demo przed użyciem środków rzeczywistych.