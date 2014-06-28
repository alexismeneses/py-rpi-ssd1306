py-rpi-ssd1306
==============

```py-rpi-ssd1306``` is a simple python driver for the SSD1306 OLED displays designed for the Raspberry PI


About SSD1306
=============

SSD1306 is a controller chip from Solomon Systech capable of driving an OLED (Organic Light Emitter Diode) panel of 128x64 pixels.
It has three serial communication modes available
- 4-wire SPI
- 3-wire SPI
- I2C
This driver uses the 4-wire SPI (ONLY)

You can easily find some OLED displays soldered with an SSD1306 on eBay.


Requirements
============

py-rpi-ssd1306 requires [py-spidev](https://github.com/doceme/py-spidev)


Wiring
======

Following is the wiring table between the Raspberry PI and the SSD1306.

```
                      P I

                    01 - 02
                    03 - 04
                    05 - 06
                    07 - 08
                    09 - 10
                    11 - 12
                    13 - 14
                    15 - 16   D/C
        VCC         17 - 18   RST
        D1 (DATA)   19 - 20
                    21 - 22
        D0 (CLK)    23 - 24   SPI CS
        GND         25 - 26
```

You can use any GPIO pins for D/C and RST (here, we use BCM23 and BCM24).
The SPI CS can also be attached to pin 26 (SPI CE1) to use the spi device bus=0/device=1

On the SSD1306, you'll need to set S1 and S2 jumper switches to 0 (GND) to enable 4-wire SPI protocol.


Enabling SPI pins
=================

On the Raspberry Pi, don't forget to enable SPI pins by removing ```spi-bcm2708``` from blacklist in ```/etc/modprobe.d/raspi-blacklist.conf```.
Beware that it will disable BCM07 to BCM11 from being raw GPIO pins.


Usage Example
=============

```
import ssd1306

lcd = ssd1306.SSD1306(spi_bus=0, spi_device=0, pin_dc=23, pin_reset=24)
lcd.hardware(remap_segment=True, alternative_com_pin=True, remap_scan_direction=True)

lcd.contrast(40)
lcd.paint()
lcd.on()

# Light all the corners
lcd.xy(0, 0)
lcd.xy(0, 63)
lcd.xy(127, 0)
lcd.xy(127, 63)
lcd.paint()

# Write some text
lcd.text(28, 28, "Hello world!", size=1)
lcd.paint()
```

You will need to call ```hardware``` method with parameters according to the real hardware layout between your SSD1306 and your OLED panel.

If you can't read Hello World on the screen, or if it's kind of upside-down, you may have to change some parameters.


Thanks
======

Thanks goes to [Guy Carpenter](https://github.com/guyc), I borrowed the font from.

