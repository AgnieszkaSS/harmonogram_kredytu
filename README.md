# Kalkulator harmonogramów spłaty kredytu (Function Calling)

Aplikacja, w której model Claude rozumie pytanie po polsku, a właściwe obliczenia
finansowe wykonuje deterministyczny kod Pythona (Function Calling / tool use).

Obsługiwane rodzaje spłaty:

- **raty równe** (annuitetowe) — co miesiąc ta sama kwota,
- **raty malejące** — stała część kapitałowa, rata maleje,
- **raty balonowe** — same odsetki przez cały okres, cały kapitał w ostatniej racie,
- **karencja** na początku kredytu: spłata samych odsetek lub kapitalizacja odsetek.

## Struktura projektu

| Plik | Opis |
|------|------|
| `obliczenia.py` | Silnik matematyczny — czysty Python, bez AI. Można uruchomić osobno. |
| `aplikacja.py` | Warstwa Function Calling: Claude rozumie pytanie i woła kalkulator. |
| `requirements.txt` | Zależności. |

## Wymagania

- Python 3.10 lub nowszy
- Klucz API z [Anthropic Console](https://console.anthropic.com/)

## Instalacja

1. (Zalecane) utwórz i aktywuj wirtualne środowisko:

   ```bash
   python -m venv venv
   source venv/bin/activate     # Linux / macOS
   venv\Scripts\activate        # Windows
   ```

2. Zainstaluj zależności:

   ```bash
   pip install -r requirements.txt
   ```

3. Ustaw klucz API w zmiennej środowiskowej:

   ```bash
   export ANTHROPIC_API_KEY="twoj-klucz"     # Linux / macOS
   setx ANTHROPIC_API_KEY "twoj-klucz"       # Windows (nowe okno terminala)
   ```

## Uruchomienie

Sam kalkulator (bez API, do sprawdzenia poprawności liczb):

```bash
python obliczenia.py
```

Pełna aplikacja z Claude:

```bash
python aplikacja.py
```

## Przykładowe zapytania

```
Policz ratę kredytu 100 000 zł, oprocentowanie 10%, na 10 lat, raty malejące z 6-miesięczną karencją tylko na odsetki.
```

```
Policz ratę kredytu 100 000 zł, oprocentowanie 10%, na 10 lat, raty annuitetowe z 3-miesięcznymi wakacjami kredytowymi.
```

```
Potrzebuję kredytu na 20000 z oprocentowaniem 5,5% na 2 lata z ratami balonowymi.
```

## Jak prezentowane są raty

Aby nie wyświetlać setek wierszy, pokazywany jest wycinek harmonogramu zależnie
od rodzaju kredytu:

- **z karencją** — pierwsza rata, pierwsza rata z kapitałem (po karencji) i ostatnia,
- **bez karencji** — trzy pierwsze i trzy ostatnie raty,
- **balonowy** — pierwsza i ostatnia (balonowa) rata.

Niezależnie od tego zwracane jest podsumowanie: liczba rat, suma odsetek
i całkowity koszt kredytu.

