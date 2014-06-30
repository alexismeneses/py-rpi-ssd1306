"""
PYTHON driver for the SSD1306 (OLED 128x64 dot-matrix controller)
this driver use the 4-wire SPI protocol to communicate
"""

import sys, os, time
import RPi.GPIO as GPIO
import spidev
import font5x8

COMMAND_ADDRESSING_MODE = 0x20
COMMAND_ADDRESSING_COLUMN = 0x21
COMMAND_ADDRESSING_PAGE = 0x22

COMMAND_ENTIRE_DISPLAY_ON_DISABLE = 0xA4
COMMAND_ENTIRE_DISPLAY_ON_ENABLE = 0xA5
COMMAND_NORMAL_DISPLAY = 0xA6
COMMAND_INVERT_DISPLAY = 0xA7
COMMAND_DISPLAY_OFF = 0xAE
COMMAND_DISPLAY_ON = 0xAF
COMMAND_CONTRAST = 0x81

COMMAND_HW_SET_DISPLAY_OFFSET = 0xD3
COMMAND_HW_SET_START_LINE = 0x40
COMMAND_HW_COM_PINS = 0xDA
COMMAND_HW_SET_MULTIPLEX = 0xA8
COMMAND_HW_DISABLE_SEGMENT_REMAP = 0xA0
COMMAND_HW_ENABLE_SEGMENT_REMAP = 0xA1
COMMAND_HW_COM_SCAN_NORMAL = 0xC0
COMMAND_HW_COM_SCAN_REMAP = 0xC8

COMMAND_TIMING_FREQ = 0xD5
COMMAND_TIMING_PRECHARGE = 0xD9

ADDRESSING_HORIZONTAL = 0x00
ADDRESSING_VERTICAL = 0x01
ADDRESSING_PAGE = 0x02

class SSD1306:
	def __init__(self, pin_dc, pin_reset, spi_bus=0, spi_device=0, buffer_pages=8, buffer_columns=128):
		self.buffer_pages = buffer_pages
		self.buffer_columns = buffer_columns
		self.pin_reset = pin_reset
		self.pin_dc = pin_dc
		self.spi = spidev.SpiDev()
		self.spi.open(spi_bus, spi_device)
		self.clear()

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.pin_dc, GPIO.OUT)
		GPIO.setup(self.pin_reset, GPIO.OUT)

		self.datamode = False
		GPIO.output(self.pin_dc, 0)

	def reset(self):
		GPIO.output(self.pin_reset, 0)
		time.sleep(0.1)
		GPIO.output(self.pin_reset, 1)

	def command(self, *bytes):
		if self.datamode:
			GPIO.output(self.pin_dc, 0)
			self.datamode = False
		self.spi.writebytes(list(bytes))

	def data(self, bytes):
		if not self.datamode:
			GPIO.output(self.pin_dc, 1)
			self.datamode = True
		self.spi.writebytes(bytes)

	def on(self):
		self.command(COMMAND_DISPLAY_ON)

	def off(self):
		self.command(COMMAND_DISPLAY_OFF)

	def inverted(self, active):
		if active:
			self.command(COMMAND_INVERT_DISPLAY)
		else:
			self.command(COMMAND_NORMAL_DISPLAY)

	def illuminate(self, active):
		if active:
			self.command(COMMAND_ENTIRE_DISPLAY_ON_ENABLE)
		else:
			self.command(COMMAND_ENTIRE_DISPLAY_ON_DISABLE)

	def hardware(self, multiplex=63, display_offset=0, start_line=0, remap_segment=False, remap_scan_direction=False, remap_leftright=False, alternative_com_pin=False):
		"""
		Hardware initialization
		This need to be called with the right parameters according to how the SEG/COM pins of the SSD1306
		are connected to the OLED panel
		"""

		self.command(COMMAND_HW_SET_MULTIPLEX, multiplex)
		self.command(COMMAND_HW_SET_DISPLAY_OFFSET, display_offset)
		self.command(COMMAND_HW_SET_START_LINE | start_line & 0x3F)

		if remap_segment:
			self.command(COMMAND_HW_ENABLE_SEGMENT_REMAP)
		else:
			self.command(COMMAND_HW_DISABLE_SEGMENT_REMAP)

		if remap_scan_direction:
			self.command(COMMAND_HW_COM_SCAN_REMAP)
		else:
			self.command(COMMAND_HW_COM_SCAN_NORMAL)

		compin = 0x02
		if alternative_com_pin:
			compin |= 0x10
		if remap_leftright:
			compin |= 0x20
		self.command(COMMAND_HW_COM_PINS, compin)

		self.command(COMMAND_TIMING_FREQ, 0b10000001)
		self.command(COMMAND_TIMING_PRECHARGE, 0x22)
		
	def page_addressing(self, page=0, column=0):
		self.command(COMMAND_ADDRESSING_MODE, ADDRESSING_PAGE)
		self.command(0xB0 | page & 0x07)
		self.command(column & 0x0F)
		self.command(0x10 | (column>>4) & 0x0F)

	def horizontal_addressing(self, pageStart=0, pageEnd=7, columnStart=0, columnEnd=127):
		self.command(COMMAND_ADDRESSING_MODE, ADDRESSING_HORIZONTAL)
		self.command(COMMAND_ADDRESSING_COLUMN, columnStart & 0x7F, columnEnd & 0x7F)
		self.command(COMMAND_ADDRESSING_PAGE, pageStart & 0x07, pageEnd & 0x07)

	def vertical_addressing(self, pageStart=0, pageEnd=7, columnStart=0, columnEnd=127):
		self.command(COMMAND_ADDRESSING_MODE, ADDRESSING_VERTICAL)
		self.command(COMMAND_ADDRESSING_COLUMN, columnStart & 0x7F, columnEnd & 0x7F)
		self.command(COMMAND_ADDRESSING_PAGE, pageStart & 0x07, pageEnd & 0x07)

	def contrast(self, value):
		self.command(COMMAND_CONTRAST, value & 0xFF)

	def xy(self, x, y, status):
		"""
		Light a pixel on or off in the buffer
		"""

		page = y // self.buffer_pages
		segbit = y % self.buffer_pages
		pos = page*self.buffer_columns + x
		segmod = 1 << segbit
		if status:
			self.buffer[pos] |= segmod
		else:
			self.buffer[pos] &= ~segmod

	def paint(self):
		"""
		Send the buffer to the SSD1306
		"""

		for p in range(0,8):
			self.page_addressing(page=p, column=0)
			pstart = p*self.buffer_columns
			pend = pstart + 128
			self.data(list([0, 0]))
			self.data(self.buffer[pstart:pend])

	def text(self, x, y, string, size=3, space=1, font=font5x8.Font5x8, invert=False, background=False):
		font_bytes = font.bytes
		font_rows = font.rows
		font_cols = font.cols
		for c in string:
			p = ord(c) * font_cols
			for col in range(0,font_cols):
				mask = font_bytes[p]
				p += 1
				py = y
				for row in range(0,8):
					for sy in range(0,size):
						px = x
						for sx in range(0,size):
							if background or (mask & 0x1 != 0):
								if not invert:
									self.xy(px, py, mask & 0x1)
								else:
									self.xy(px, py, (~mask) & 0x1)
							px += 1
						py += 1
					mask >>= 1
				x += size
			x += space

	def clear(self):
		"""
		Clear the buffer
		"""

		buffersize = self.buffer_pages * self.buffer_columns
		self.buffer = [0] * buffersize

	def shift_left(self, n=1):
		old_buffer = list(self.buffer)
		self.buffer = []
		for p in range(0,self.buffer_pages):
			pstart = p*self.buffer_columns
			pend = pstart + self.buffer_columns
			self.buffer = self.buffer + old_buffer[pstart+n:pend] + old_buffer[pstart:pstart+n]

	def shift_right(self, n=1):
		old_buffer = list(self.buffer)
		self.buffer = []
		for p in range(0,self.buffer_pages):
			pstart = p*self.buffer_columns
			pend = pstart + self.buffer_columns
			self.buffer = self.buffer + old_buffer[pend-n:pend] + old_buffer[pstart:pend-n]

	def shift_up(self, n=1):
		shift_page = n // 8
		shift_seg = n % 8
		if shift_page > 0:
			old_buffer = self.buffer[:]
			self.buffer = []
			for p in range (0,self.buffer_pages):
				old_p = (p + shift_page) % self.buffer_pages
				pstart = old_p*self.buffer_columns
				pend = pstart + self.buffer_columns
				self.buffer = self.buffer + old_buffer[pstart:pend]
		if shift_seg > 0:
			old_buffer = self.buffer[:]
			back_shift_seg = 8 - shift_seg
			mask = 2**back_shift_seg - 1
			back_mask = 0xFF - mask
			for p in range (0,self.buffer_pages):
				for c in range(0,self.buffer_columns):
					pos = p * self.buffer_columns + c
					next_p = (p + 1) % self.buffer_pages
					next_pos = next_p * self.buffer_columns + c
					self.buffer[pos] = (old_buffer[pos] >> shift_seg) & mask | (old_buffer[next_pos] << back_shift_seg) & back_mask

	def shift_down(self, n=1):
		shift_page = n // 8
		shift_seg = n % 8
		if shift_page > 0:
			old_buffer = self.buffer[:]
			self.buffer = []
			for p in range (0,self.buffer_pages):
				old_p = (self.buffer_pages + p - shift_page) % self.buffer_pages
				pstart = old_p*self.buffer_columns
				pend = pstart + self.buffer_columns
				self.buffer = self.buffer + old_buffer[pstart:pend]
		if shift_seg > 0:
			old_buffer = self.buffer[:]
			back_shift_seg = 8 - shift_seg
			back_mask = 2**shift_seg - 1
			mask = 0xFF - back_mask
			for p in range (0,self.buffer_pages):
				for c in range(0,self.buffer_columns):
					pos = p * self.buffer_columns + c
					next_p = (self.buffer_pages + p - 1) % self.buffer_pages
					next_pos = next_p * self.buffer_columns + c
					self.buffer[pos] = (old_buffer[pos] << shift_seg) & mask | (old_buffer[next_pos] >> back_shift_seg) & back_mask

	def set_buffer_size(self,x,y):
		self.buffer_pages = y // 8
		if y % 8 > 0:
			self.buffer_pages += 1
                self.buffer_columns = x
		self.clear()

