"""
APLIKACJA: CLAUDE + FUNCTION CALLING
====================================
Claude rozumie pytanie po polsku, wyłapuje z niego liczby i woła nasz kalkulator z pliku obliczenia.py.
Uruchomienie:
    python aplikacja.py
"""

import json
import anthropic
from obliczenia import oblicz_harmonogram

# 1. OPIS NARZĘDZIA — to jest jedyne, co "widzi" Claude o naszym kalkulatorze.
NARZEDZIA = [
    {
        "name": "oblicz_harmonogram_splaty",
        "description": (
            "Oblicza harmonogram spłaty kredytu. Obsługuje raty równe, malejące "
            "i balonowe (same odsetki przez cały okres, cały kapitał w ostatniej racie) "
            "oraz karencję (okres ulgi na początku). Zwraca podsumowanie kosztów."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kwota_kredytu": {
                    "type": "number", "description": "Kapitał w PLN, np. 300000"
                },
                "oprocentowanie_roczne": {
                    "type": "number", "description": "Stopa nominalna w % rocznie, np. 7.2"
                },
                "liczba_rat": {
                    "type": "integer", "description": "Łączna liczba rat/miesięcy (wliczając karencję)"
                },
                "typ_rat": {
                    "type": "string", "enum": ["rowne", "malejace", "balonowe"]
                },
                "karencja_miesiace": {
                    "type": "integer", "description": "Liczba miesięcy karencji, 0 jeśli brak"
                },
                "typ_karencji": {
                    "type": "string", "enum": ["brak", "tylko_odsetki", "wakacje_kredytowe"]
                },
            },
            "required": ["kwota_kredytu", "oprocentowanie_roczne", "liczba_rat", "typ_rat"],
        },
    }
]

def opisz_rate(x):
    return {
        "nr": x.nr,
        "rata": round(x.rata, 2),
        "kapital": round(x.kapital, 2),
        "odsetki": round(x.odsetki, 2),
        "saldo_po": round(x.saldo_po, 2),
    }

def wykonaj_narzedzie(nazwa, argumenty):
    if nazwa != "oblicz_harmonogram_splaty":
        return {"blad": f"Nieznane narzędzie: {nazwa}"}
    try:
        wynik = oblicz_harmonogram(
            kwota_kredytu=argumenty["kwota_kredytu"],
            oprocentowanie_roczne=argumenty["oprocentowanie_roczne"],
            liczba_rat=argumenty["liczba_rat"],
            typ_rat=argumenty["typ_rat"],
            karencja_miesiace=argumenty.get("karencja_miesiace", 0),
            typ_karencji=argumenty.get("typ_karencji", "brak"),
        )
    except Exception as e:
        # Błąd odsyłamy modelowi — sam go ładnie wyjaśni użytkownikowi.
        return {"blad": str(e)}
 
    # Wybór rat do pokazania zależy od rodzaju kredytu.
    h = wynik["harmonogram"]
    typ_rat = argumenty["typ_rat"]
    ma_karencje = (argumenty.get("karencja_miesiace", 0) > 0
                   and argumenty.get("typ_karencji", "brak") != "brak")
 
    if typ_rat == "balonowe":
        # tylko pierwsza i ostatnia (balonowa) rata
        wybrane = [h[0], h[-1]]
    elif ma_karencje:
        # pierwsza rata, pierwsza rata z kapitałem (po karencji) i ostatnia
        pierwsza_z_kapitalem = next((x for x in h if x.kapital > 0), h[-1])
        wybrane = [h[0], pierwsza_z_kapitalem, h[-1]]
    else:
        # bez karencji: trzy pierwsze i trzy ostatnie raty
        wybrane = h[:3] + h[-3:]
 
    # usunięcie ewentualnych duplikatów (krótkie kredyty), z zachowaniem kolejności
    wybrane = list({x.nr: x for x in wybrane}.values())
 
    return {
        "raty": [opisz_rate(x) for x in wybrane],
        "liczba_rat": len(h),
        "suma_odsetek": round(wynik["suma_odsetek"], 2),
        "calkowity_koszt": round(wynik["calkowity_koszt"], 2),
    }
 
class Chatbot:
    def __init__(self, model : str, system_prompt : str, max_tokens : int):
        self.context = []
        self.model = model
        self.tools = NARZEDZIA
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        
        #klucz czytany z ANTHROPIC_API_KEY
        self.client = anthropic.Anthropic()
      
    def extend_context(self, side, content):
        self.context.append({"role": side, "content": content})
      
    # 3. PĘTLA AGENTOWA — serce Function Calling.
    def query(self, user_input): 
        self.extend_context("user", user_input)
        
        while True:
            odpowiedz = self.client.messages.create(
                model = self.model,
                max_tokens = self.max_tokens,
                system = self.system_prompt,
                tools = NARZEDZIA,
                messages = self.context,
            )

            # zapamiętujemy odpowiedź modelu (API jest bezstanowe!)
            self.extend_context("assistant", odpowiedz.content)
        
            # Claude skończył i nie chce już narzędzia -> zwracamy tekst.
            if odpowiedz.stop_reason != "tool_use":
                return "".join(b.text for b in odpowiedz.content if b.type == "text")

            # Claude poprosił o narzędzie -> wykonujemy i odsyłamy wynik.
            wyniki = []
            for blok in odpowiedz.content:
                if blok.type == "tool_use":
                    rezultat = wykonaj_narzedzie(blok.name, blok.input)
                    wyniki.append({
                        "type": "tool_result",
                        "tool_use_id": blok.id,
                        "content": json.dumps(rezultat, ensure_ascii=False),
                    })
        
            self.extend_context("user", wyniki)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
SYSTEM_PROMPT = "Jesteś doradcą kredytowym. Do WSZYSTKICH obliczeń ZAWSZE używaj narzędzia, nigdy nie licz w pamięci. Wynik wyjaśnij prosto, po polsku. Wyniki są wyświetlane w terminalu windows, zatem nie używaj formatu markdown i emoji."

def main():
    chatbot = Chatbot(MODEL, SYSTEM_PROMPT, MAX_TOKENS)
    print("Witaj w kalkulatorze harmonogramu spłat kredytu.\nOpisz swój kredyt w celu obliczenia harmonogramu.");
    while(True):
        print("\n================== Użytkownik ==================\n" )
        pytanie = input()
        print("\n================== Asystent ==================\n\n", chatbot.query(pytanie))
        
if __name__ == "__main__":
    main()
