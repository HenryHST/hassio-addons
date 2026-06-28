# ha-chronyd (archived)

This repository is **archived**. Development continues as a Home Assistant add-on:

**https://github.com/henryhst/hassio-addons/tree/main/chronyd**

## Install as Home Assistant add-on

1. Add repository: `https://github.com/henryhst/hassio-addons`
2. Install **Chrony NTP** from the add-on store
3. See [DOCS.md](https://github.com/henryhst/hassio-addons/blob/main/chronyd/DOCS.md)

## Standalone Docker

For non-Home-Assistant use, build from the add-on directory in hassio-addons:

```bash
git clone https://github.com/henryhst/hassio-addons.git
cd hassio-addons/chronyd
docker compose up -d
```

## ESP32 firmware

Reference-clock sketches are in `chronyd/ESP32/` in [hassio-addons](https://github.com/henryhst/hassio-addons).

## License

MIT License
