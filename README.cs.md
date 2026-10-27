# CestujOK – odjezdy autobusů pro Home Assistant

Samostatný doplněk pro Home Assistant OS, který načítá nadcházející autobusové odjezdy z portálu CestujOK / IDSOK a publikuje je do Home Assistantu pomocí MQTT Discovery.

**Výchozí zastávka:** Jeseník, Lipovská (ID `S-13053`).

**Language:** [English README](README.md)

## Funkce

- Ve výchozím nastavení načítá nadcházející odjezdy každých 60 sekund.
- Vytváří MQTT Discovery senzory pro jednotlivé odjezdy (výchozí počet je 6).
- Čas odjezdu je stav senzoru; další údaje jsou dostupné v atributech: směr/cíl, označení linky nebo spoje, zpoždění, typ vozidla, typ linky a příznak objížďky.
- Publikuje dostupnost přes MQTT a uchovává poslední stav jako retained zprávu.
- Lze ho aktualizovat nebo restartovat samostatně, bez restartu Home Assistant Core.

## Instalace

1. V Home Assistantu otevři **Nastavení → Doplňky → Obchod s doplňky**.
2. V nabídce vpravo nahoře vyber **Repozitáře**.
3. Přidej tento repozitář: https://github.com/Marthinek/HA-odjezdybusOL
4. Obnov obchod s doplňky a nainstaluj **CestujOK – Odjezdy autobusů**.
5. Nastav MQTT broker. Pokud používáš doplněk Mosquitto, hostitel bývá `core-mosquitto` a port `1883`. Zadej uživatelské jméno a heslo podle své konfigurace MQTT.
6. Spusť doplněk. Senzory by se měly automaticky objevit díky MQTT Discovery.

## Konfigurace

- `station_id`: ID zastávky v CestujOK; výchozí hodnota je `S-13053`.
- `station_name`: název zastávky zobrazovaný v Home Assistantu.
- `update_interval`: interval dotazování v sekundách (30–600).
- `departures_count`: počet senzorů odjezdů (1–10).
- `mqtt_host`, `mqtt_port`, `mqtt_username`, `mqtt_password`: nastavení připojení k MQTT.
- `mqtt_discovery_prefix`: prefix MQTT Discovery, obvykle `homeassistant`.
- `mqtt_topic_prefix`: prefix MQTT témat doplňku; výchozí hodnota je `cestujok`.

Pro jinou zastávku změň `station_id` i `station_name`. Například **Jeseník, žel.st.** má ID `S-13064` a **Jeseník, Lipovská** má ID `S-13053`.

## Zdroj dat a omezení

V síťové komunikaci webu CestujOK byly identifikovány tyto endpointy:

- `GET https://www.cestujok.cz/idspublicservices/api/station` — seznam zastávek.
- `GET https://www.cestujok.cz/idspublicservices/api/station/S-13053/nextservices` — nadcházející odjezdy pro zastávku Jeseník, Lipovská.

Doplněk používá neoficiální HTTP rozhraní, které se může bez upozornění změnit a jehož funkčnost provozovatel negarantuje. Informace o zpoždění nemusí být dostupná u každého spoje. Projekt není oficiálně spojen s CestujOK, IDSOK ani žádným dopravcem.

## Původní HACS integrace

Původní experimentální HACS integrace zůstává v adresáři `custom_components/cestujok_departures`. Pro samostatné aktualizace doporučujeme používat doplněk a MQTT Discovery.

Do veřejných issue nevkládej cookies, autorizační hlavičky, tokeny ani neupravené HAR soubory.
