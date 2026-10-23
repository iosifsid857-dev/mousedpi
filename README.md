# MouseDPI

A tiny settings app for gaming mice on Linux: DPI levels, report rate and lighting. It talks to
[libratbag](https://github.com/libratbag/libratbag), so you don't need Logitech G HUB or a Windows VM. Settings are
written to the mouse's own memory, so they keep working in any OS and any game.

> The interface is in Russian for now. Russian README: [README.ru.md](README.ru.md).

Tested on a **Logitech G502 HERO**. Other mice that libratbag supports should work too.

* **DPI**: up to 5 levels per profile, any value the sensor supports. You can enable or disable levels and choose
  the current one.
* **Report rate**: 125 to 1000 Hz.
* **Lighting**: solid, breathing, color cycle or off, with any color, for each LED.
* **Profiles**: edit any onboard profile and make it active.

## Install

```
sudo dnf install libratbag-ratbagd python3-pyside6     # Debian/Ubuntu: ratbagd, python3-pyside6
sudo systemctl enable --now ratbagd
git clone https://github.com/iosifsid857-dev/mousedpi && cd mousedpi
python3 mousedpi.py
```

## Support

If MouseDPI helped, you can support the author: [Monobank jar](https://send.monobank.ua/jar/ABkwFDAY2V).

MIT license. MouseDPI is a front-end to libratbag/ratbagctl. It is not affiliated with Logitech. It was developed
with Claude (Anthropic) as a coding assistant.
