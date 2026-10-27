# HA odjezdy busů – CestujOK / IDSOK

Experimentální integrace Home Assistantu pro odjezdy autobusů z vybrané zastávky na portálu CestujOK.

> **Stav: experimentální.** Používá neoficiální HTTP rozhraní, které se může změnit. Vyhledávání zastávek a zpoždění se musí ověřit proti aktuálním odpovědím webu.

## Funkce
- Vyhledání a výběr zastávky při přidání integrace, ne pevně nastavená Lipovská.
- Senzor s počtem odjezdů a seznamem spojů v atributech.
- Pokus o doplnění zpoždění z rozhraní živých poloh vozidel.
- Aktualizace každou minutu.

## Instalace přes HACS (Custom repository)
1. HACS → Integrations → ⋮ → Custom repositories.
2. Přidej `https://github.com/Marthinek/HA-odjezdybusOL`, kategorii **Integration**.
3. Nainstaluj a restartuj Home Assistant.
4. Nastavení → Zařízení a služby → Přidat integraci → CestujOK – Odjezdy autobusů.
5. Zadej název zastávky nebo města a vyber správnou zastávku.

## Omezení
- Rozhraní CestujOK není pro tento projekt veřejně zdokumentované ani garantované.
- Endpoint vyhledávání a struktury živých dat mohou vyžadovat úpravu podle skutečných odpovědí webu.
- Zpoždění nemusí být dostupné u každého spoje.
- Projekt není oficiálně spojen s CestujOK, IDSOK ani dopravci.

Neposílej do veřejných issue cookies, autorizační hlavičky, tokeny ani neupravené HAR soubory.
