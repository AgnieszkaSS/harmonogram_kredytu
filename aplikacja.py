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
#    Dobre opisy = model trafnie wybiera funkcję i argumenty.
NARZEDZIA = [
    {
        "name": "oblicz_harmonogram_splaty",
        "description": (
            "Oblicza harmonogram spłaty kredytu. Obsługuje raty równe i malejące "
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
                    "type": "string", "enum": ["rowne", "malejace"]
                },
                "karencja_miesiace": {
                    "type": "integer", "description": "Liczba miesięcy karencji, 0 jeśli brak"
                },
                "typ_karencji": {
                    "type": "string", "enum": ["brak", "tylko_odsetki", "kapitalizacja"]
                },
            },
            "required": ["kwota_kredytu", "oprocentowanie_roczne", "liczba_rat", "typ_rat"],
        },
    }
]

# 2. WYKONANIE NARZĘDZIA — łączymy nazwę od Claude'a z prawdziwą funkcją.
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

    # Modelowi dajemy STRESZCZENIE, a nie 360 wierszy — to oszczędza tokeny.
    h = wynik["harmonogram"]
    return {
        "pierwsza_rata": round(h[0].rata, 2),
        "ostatnia_rata": round(h[-1].rata, 2),
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
SYSTEM_PROMPT = "Jesteś doradcą kredytowym. Do WSZYSTKICH obliczeń ZAWSZE używaj narzędzia, nigdy nie licz w pamięci. Wynik wyjaśnij prosto, po polsku. Wyniki są wyświetlane w terminalu windows, zatem nie używaj formatu markdown i emoji."
MAX_TOKENS = 1024

def main():
    print("Witaj w kalkulatorze harmonogramu spłat kredytu.\nOpisz swój kredyt w celu obliczenia harmonogramu.");
    #pytanie = ("Policz ratę kredytu 300 000 zł, oprocentowanie 7%, na 30 lat, "
    #           "raty malejące, z 6-miesięczną karencją tylko na odsetki.")
   
    chatbot = Chatbot(MODEL, SYSTEM_PROMPT, MAX_TOKENS)
   
    while(True):
        print("\n================== Użytkownik ==================\n" )
        pytanie = input()
        print("\n================== Asystent ==================\n", chatbot.query(pytanie))
        
if __name__ == "__main__":
    main()
