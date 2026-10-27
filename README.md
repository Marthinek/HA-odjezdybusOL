# CestujOK – odjezdy autobusů pro Home Assistant

Samostatný Home Assistant OS doplněk (app), který čte odjezdy z portálu CestujOK / IDSOK a publikuje je do Home Assistantu přes MQTT Discovery.

**Výchozí zastávka:** Jeseník, Lipovská (ID S-13053).

## Co doplněk dělá

- Každých 60 sekund načítá seznam nejbližších odjezdů ze zastávky.
- Publikuje MQTT Discovery senzory pro jednotlivé odjezdy (výchozí počet: 6).
- U každého senzoru zpřístupňuje jako atributy cíl, označení spoje, čas, zpoždění, typ vozidla a informaci o výluce.
- Publikuje dostupnost přes MQTT a uchovává poslední stav jako retained zprávu.
- Doplněk lze aktualizovat nebo restartovat samostatně, bez restartu Home Assistant Core.

## Instalace doplňku

1. Otevři **Nastavení → Doplňky → Obchod s doplňky**.
2. V nabídce vpravo nahoře zvol **Repozitáře**.
3. Přidej tento repozitář: https://github.com/Marthinek/HA-odjezdybusOL
4. Obnov stránku obchodu a nainstaluj **CestujOK – Odjezdy autobusů**.
5. V konfiguraci doplňku nastav MQTT broker. Pokud používáš Mosquitto add-on, obvykle je hostitel core-mosquitto, port 1883; doplň MQTT uživatelské jméno a heslo podle své konfigurace.
6. Spusť doplněk. Senzory se mají objevit v Home Assistantu automaticky díky MQTT Discovery.

## Konfigurace

- station_id: ID zastávky v CestujOK, výchozí S-13053.
- station_name: název zastávky zobrazený v Home Assistantu.
- update_interval: interval dotazování v sekundách (30–600).
- departures_count: počet senzorů odjezdů (1–10).
- mqtt_host, mqtt_port, mqtt_username, mqtt_password: připojení k MQTT.
- mqtt_discovery_prefix: obvykle homeassistant.
- mqtt_topic_prefix: prefix témat doplňku, výchozí cestujok.

Pro zastávku Jeseník, Lipovská je ID v CestujOK S-13053. Pokud chceš jinou zastávku, změň station_id i station_name.

## Zdroj dat a omezení

Použité endpointy byly ověřeny v síťovém záznamu webu CestujOK:

- GET https://www.cestujok.cz/idspublicservices/api/station – seznam zastávek.
- GET https://www.cestujok.cz/idspublicservices/api/station/S-13053/nextservices – nadcházející odjezdy včetně pole delay, pokud je dostupné.

Jde o neoficiální HTTP rozhraní, které se může kdykoli změnit a není garantováno provozovatelem. Zpoždění není uvedeno u každého spoje. Projekt není oficiálně spojen s CestujOK, IDSOK ani dopravci.

## Starší HACS integrace

V adresáři custom_components/cestujok_departures zůstala původní experimentální HACS integrace. Pro samostatné aktualizace doporučujeme používat tento doplněk a MQTT Discovery.

Neposílej do veřejných issue cookies, autorizační hlavičky, tokeny ani neupravené HAR soubory.
