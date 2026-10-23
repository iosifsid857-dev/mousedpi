# MouseDPI

Маленькая программа для игровой мышки на Linux: DPI, частота опроса и подсветка. Работает через libratbag,
поэтому Logitech G HUB не нужен. Настройки записываются в память самой мышки и работают в любой системе и игре.

Проверено на **Logitech G502 HERO**. Другие мышки, которые поддерживает libratbag, тоже должны работать.

* **DPI:** до 5 уровней на профиль. Можно включать и выключать уровни и выбирать текущий.
* **Частота опроса:** от 125 до 1000 Гц.
* **Подсветка:** горит, дышит, радуга или выключена, любой цвет.
* **Профили:** все профили из памяти мышки.

## Установка

```
sudo dnf install libratbag-ratbagd python3-pyside6
sudo systemctl enable --now ratbagd
git clone https://github.com/iosifsid857-dev/mousedpi && cd mousedpi
python3 mousedpi.py
```

## Поддержать автора

[Банка Monobank](https://send.monobank.ua/jar/ABkwFDAY2V)
