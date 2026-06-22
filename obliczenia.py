"""
KALKULATOR HARMONOGRAMÓW SPŁATY KREDYTU
=======================================
Czysty Python - same liczby, zero AI.
Ten plik można uruchomić i przetestować samodzielnie:  python obliczenia.py
"""

from dataclasses import dataclass


@dataclass
class Rata:
    """Jeden wiersz harmonogramu."""
    nr: int            # numer raty
    rata: float        # ile płacisz w tym miesiącu
    kapital: float     # część spłacająca dług
    odsetki: float     # część będąca kosztem (odsetkami)
    saldo_po: float    # ile długu zostaje po tej racie


def licz_raty(saldo, liczba_rat, r, typ_rat, nr_start=1):
    """
    'Normalna' faza spłaty (po ewentualnej karencji).
    saldo      - kwota do spłaty na start tej fazy
    liczba_rat - ile rat zostało
    r          - miesięczna stopa procentowa (np. 7%/rok -> 0.07/12)
    typ_rat    - 'rowne' albo 'malejace'
    """
    raty = []
    if liczba_rat <= 0:
        return raty

    if typ_rat == "rowne":
        # Stała rata annuitetowa. Uwaga na r == 0 (dzielenie przez zero!).
        if r == 0:
            rata_stala = saldo / liczba_rat
        else:
            rata_stala = saldo * (r * (1 + r) ** liczba_rat) / ((1 + r) ** liczba_rat - 1)
        for i in range(liczba_rat):
            odsetki = saldo * r
            kapital = rata_stala - odsetki
            saldo -= kapital
            raty.append(Rata(nr_start + i, rata_stala, kapital, odsetki, saldo))

    elif typ_rat == "malejace":
        # Część kapitałowa jest stała, odsetki maleją wraz z saldem.
        kapital_staly = saldo / liczba_rat
        for i in range(liczba_rat):
            odsetki = saldo * r
            rata = kapital_staly + odsetki
            saldo -= kapital_staly
            raty.append(Rata(nr_start + i, rata, kapital_staly, odsetki, saldo))

    elif typ_rat == "balonowe":
        # Kredyt balonowy: przez cały okres płacisz SAME odsetki (dług stoi),
        # a cały kapitał oddajesz jednorazowo w ostatniej (balonowej) racie.
        for i in range(liczba_rat):
            odsetki = saldo * r
            kapital = saldo if i == liczba_rat - 1 else 0.0  # tylko ostatnia rata
            rata = kapital + odsetki
            saldo -= kapital
            raty.append(Rata(nr_start + i, rata, kapital, odsetki, saldo))
    else:
        raise ValueError(f"Nieznany typ rat: {typ_rat}")

    return raty


def oblicz_harmonogram(kwota_kredytu, oprocentowanie_roczne, liczba_rat,
                       typ_rat="rowne", karencja_miesiace=0, typ_karencji="brak"):
    """
    Główna funkcja. Zwraca słownik z pełnym harmonogramem i podsumowaniem kosztów.

    typ_rat:
      'rowne'    - co miesiąc ta sama rata (annuitetowa)
      'malejace' - stała część kapitałowa, rata maleje
      'balonowe' - same odsetki przez cały okres, cały kapitał w ostatniej racie

    typ_karencji:
      'brak'          - bez karencji
      'tylko_odsetki' - w karencji płacisz same odsetki, dług się nie zmienia
      'wakacje_kredytowe' - w karencji nie płacisz nic, odsetki doliczają się do długu
    Uwaga: liczba_rat to ŁĄCZNA liczba miesięcy, wliczając karencję.
    """
    # --- walidacja (przypadki brzegowe) ---
    if kwota_kredytu <= 0:
        raise ValueError("Kwota kredytu musi być dodatnia.")
    if liczba_rat <= 0:
        raise ValueError("Liczba rat musi być dodatnia.")
    if karencja_miesiace >= liczba_rat:
        raise ValueError("Karencja nie może obejmować wszystkich rat.")

    r = oprocentowanie_roczne / 100 / 12   # stopa miesięczna
    harmonogram = []
    saldo = kwota_kredytu
    nr = 1

    # --- FAZA KARENCJI ---
    if karencja_miesiace > 0 and typ_karencji != "brak":
        for _ in range(karencja_miesiace):
            odsetki = saldo * r
            if typ_karencji == "tylko_odsetki":
                # płacisz odsetki, dług bez zmian
                harmonogram.append(Rata(nr, odsetki, 0.0, odsetki, saldo))
            elif typ_karencji == "wakacje_kredytowe":
                # nie płacisz nic, odsetki powiększają dług
                saldo += odsetki
                harmonogram.append(Rata(nr, 0.0, 0.0, odsetki, saldo))
            else:
                raise ValueError(f"Nieznany typ karencji: {typ_karencji}")
            nr += 1

    # --- FAZA WŁAŚCIWEJ SPŁATY ---
    pozostale_raty = liczba_rat - karencja_miesiace
    harmonogram += licz_raty(saldo, pozostale_raty, r, typ_rat, nr_start=nr)

    # --- podsumowanie ---
    suma_odsetek = sum(x.odsetki for x in harmonogram)
    calkowity_koszt = sum(x.rata for x in harmonogram)

    return {
        "harmonogram": harmonogram,
        "suma_odsetek": suma_odsetek,
        "calkowity_koszt": calkowity_koszt,
        "kwota_kredytu": kwota_kredytu,
    }


# --- szybki test: uruchom ten plik bezpośrednio ---
if __name__ == "__main__":
    wynik = oblicz_harmonogram(
        kwota_kredytu=300000,
        oprocentowanie_roczne=7,
        liczba_rat=360,              # 30 lat
        typ_rat="malejace",
        karencja_miesiace=6,
        typ_karencji="tylko_odsetki",
    )

    print("Pierwsze 10 rat:")
    for x in wynik["harmonogram"][:10]:
        print(f"  Rata {x.nr:>3}: {x.rata:>10.2f} zł  "
              f"(kapitał {x.kapital:>9.2f}, odsetki {x.odsetki:>8.2f}, saldo {x.saldo_po:>11.2f})")

    print(f"\nSuma odsetek:    {wynik['suma_odsetek']:>12.2f} zł")
    print(f"Całkowity koszt: {wynik['calkowity_koszt']:>12.2f} zł")