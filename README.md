# Netzspannungs-Monitoring (DIN EN 50160)

Dieses Repository dokumentiert systematische Grenzwertunterschreitungen der Netzspannung am Hausanschluss.

## Kernergebnis
Die Messungen belegen Spannungseinbrüche bis auf **201,4 V** (Normgrenze: 207 V). Diese korrelieren unmittelbar mit Ausfällen von Haushaltsgeräten.

## Inhalt
* [Bericht zur technischen Analyse und Auswertung](https://github.com/toszlanyi/LangzeitmessungWestnetz/blob/main/Bericht%20zur%20%C3%9Cberpr%C3%BCfung%20der%20Spannungsqualit%C3%A4t%202026-02-01.pdf)
* [Rohdaten der Langzeitmessung (Intervall: 10 Sek. / 2 Min. Aggregation)](https://github.com/toszlanyi/LangzeitmessungWestnetz/blob/main/solar_log_v3_minmax.csv)
* [Python-Skript zur Datenerhebung (Modbus/TCP)](https://github.com/toszlanyi/LangzeitmessungWestnetz/blob/main/langzeit.py)
* [Videodokumentation der Geräteausfälle synchron zu den Messdaten](https://github.com/toszlanyi/LangzeitmessungWestnetz/raw/refs/heads/main/Kochfeld%202026-01-29%2012:10.mp4)

Videodokumentation der Geräteausfälle synchron zu den Messdaten

<video src="https://github.com/toszlanyi/LangzeitmessungWestnetz/raw/refs/heads/main/Kochfeld%202026-01-29%2012:10.mp4" controls="controls" style="max-width: 100%;">
</video>

## Technik
* **Hardware:** Eastron SDM630 MCT (Klasse 1), Waveshare RS485-TO-ETH (B) & Raspberry Pi 4.
* **Methodik:** Kontinuierliches Logging der Phasenströme und -spannungen zur Identifikation von Netzimpedanzproblemen.

---
*Hinweis: Private Dokumentation zur Vorlage beim Netzbetreiber (Westnetz).*
