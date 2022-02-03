import time

import displayio
import board
import terminalio
import json
from adafruit_display_text import bitmap_label
from audiomp3 import MP3Decoder
import sys
import os
import adafruit_sdcard
import board
import busio
import digitalio
import storage

try:
    from audioio import AudioOut
except ImportError:
    try:
        from audiopwmio import PWMAudioOut as AudioOut
    except ImportError:
        pass  # not always supported by every board!

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.SD_CS)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
sys.path.append("/sd")

print(os.listdir("/sd"))

# You have to specify some mp3 file when creating the decoder
# mp3 = open("/sd/trvium/01 Brave This Storm.mp3", "rb")
# decoder = MP3Decoder(mp3)
# audio = AudioOut(board.SPEAKER)
# audio.play(decoder)

PLAYLIST_FILE = "playlist.json"
SKIN_IMAGE = "/base_240x320.bmp"
SKIN_CONFIG_FILE = "base_config.json"




class ScrollingLabel(bitmap_label.Label):
    def __init__(self, font, max_characters=10, full_text="", animate_time=0.3, current_index=0, **kwargs):
        super().__init__(font, **kwargs)
        self.animate_time = animate_time
        self._current_index = current_index
        self._last_animate_time = -1
        self.max_characters = max_characters
        if "text" in kwargs:
            raise ValueError("User code should not set the text argument on ScrollingText. Use full_text instead.")
        else:
            if full_text[-1] != " ":
                full_text = "{} ".format(full_text)
            self._full_text = full_text

        self.update()

    def update(self, force=False):
        _now = time.monotonic()
        if force or self._last_animate_time + self.animate_time <= _now:

            if len(self.full_text) <= self.max_characters:
                self.text = self.full_text
                self._last_animate_time = _now
                return
            else:
                if self.current_index + self.max_characters <= len(self.full_text):
                    _showing_string = self.full_text[self.current_index: self.current_index + self.max_characters]
                else:
                    _showing_string_start = self.full_text[self.current_index:]
                    _showing_string_end = "{}".format(
                        self.full_text[:(self.current_index + self.max_characters) % len(self.full_text)])

                    _showing_string = "{}{}".format(_showing_string_start, _showing_string_end)
                self.text = _showing_string

                self.current_index += 1
                self._last_animate_time = _now

                return

    @property
    def current_index(self):
        return self._current_index

    @current_index.setter
    def current_index(self, new_index):
        if new_index < len(self.full_text):
            self._current_index = new_index
        else:
            self._current_index = new_index % len(self.full_text)

        # self.update()

    @property
    def full_text(self):
        return self._full_text

    @full_text.setter
    def full_text(self, new_text):
        self._full_text = new_text
        self.update()


class PlaylistDisplay(displayio.Group):
    def __init__(self, text_color, song_list=[], current_track_number=0):
        super().__init__()

        # song_list.append("Dj Mike Llama - Llama Whippin")
        # song_list.append("Baby Metal - Gimme Chocolate!!")
        # song_list.append("Baby Metal - Pa Pa Ya!!")
        # song_list.append("Baby Metal - KARATE")
        # song_list.append("Baby Metal - Headbangeeeeerrrrr!!!!!")

        self._song_list = song_list
        self._current_track_number = current_track_number

        self._label = bitmap_label.Label(terminalio.FONT, color=text_color)

        self._label.anchor_point = (0, 0)
        self._label.anchored_position = (0, 0)
        self.append(self._label)

        self.update_display()

    def update_display(self):
        _showing_songs = self.song_list[self.current_track_number - 1:self.current_track_number + 3 - 1]

        _showing_string = ""
        for index, song in enumerate(_showing_songs):
            _cur_line = "{}. {}".format(self.current_track_number + index, song[:30])
            _showing_string = "{}{}\n".format(_showing_string, _cur_line)

        # _showing_string = "{}\n{}\n{}".format(
        #     "{}. {}".format(self.current_song_index + 1, _showing_songs[0][:30]),
        #     "{}. {}".format(self.current_song_index + 2, _showing_songs[1][:30]),
        #     "{}. {}".format(self.current_song_index + 3, _showing_songs[2][:30]),
        # )
        self._label.text = _showing_string

    @property
    def song_list(self):
        return self._song_list

    @song_list.setter
    def song_list(self, new_song_list):
        self._song_list = new_song_list
        self.update_display()

    def from_files_list(self, files_list):
        _song_list = []
        for _file in files_list:
            _song_list.append(_file.split("/")[-1].replace(".mp3", ""))
        self.song_list = _song_list

    @property
    def current_track_number(self):
        return self._current_track_number

    @current_track_number.setter
    def current_track_number(self, new_index):
        if new_index <= len(self.song_list):
            self._current_track_number = new_index
        else:
            self._current_track_number = new_index % len(self.song_list)
        self.update_display()

    @property
    def current_track_title(self):
        if self.current_track_number == 0:
            return "1. {}".format(self.song_list[0])
        else:
            return "{}. {}".format(self.current_track_number,self.song_list[self.current_track_number-1])


class ClockDisplay(displayio.Group):
    def __init__(self, text_color):
        super().__init__()

        self._seconds = 3
        self.first_digit = bitmap_label.Label(terminalio.FONT, color=text_color)
        self.first_digit.anchor_point = (0, 0)
        self.first_digit.anchored_position = (0, 0)
        self.append(self.first_digit)

        self.second_digit = bitmap_label.Label(terminalio.FONT, color=text_color)
        self.second_digit.anchor_point = (0, 0)
        self.second_digit.anchored_position = (10, 0)
        self.append(self.second_digit)

        self.third_digit = bitmap_label.Label(terminalio.FONT, color=text_color)
        self.third_digit.anchor_point = (0, 0)
        self.third_digit.anchored_position = (26, 0)
        self.append(self.third_digit)

        self.fourth_digit = bitmap_label.Label(terminalio.FONT, color=text_color)
        self.fourth_digit.anchor_point = (0, 0)
        self.fourth_digit.anchored_position = (36, 0)
        self.append(self.fourth_digit)
        self.update_display()

    @property
    def seconds(self):
        return self._seconds

    @seconds.setter
    def seconds(self, new_seconds_value):
        self._seconds = new_seconds_value
        self.update_display()

    def update_display(self):
        _minutes = self.seconds // 60
        _seconds = self.seconds % 60

        _minutes_str = f'{_minutes:02}'
        _seconds_str = f'{_seconds:02}'

        if self.first_digit.text != _minutes_str[0]:
            self.first_digit.text = _minutes_str[0]

        if self.second_digit.text != _minutes_str[1]:
            self.second_digit.text = _minutes_str[1]

        if self.third_digit.text != _seconds_str[0]:
            self.third_digit.text = _seconds_str[0]

        if self.fourth_digit.text != _seconds_str[1]:
            self.fourth_digit.text = _seconds_str[1]


display = board.DISPLAY
display.rotation = 90

f = open(SKIN_CONFIG_FILE, "r")
CONFIG_DATA = json.loads(f.read())
f.close()

f = open(PLAYLIST_FILE, "r")
PLAYLIST = json.loads(f.read())
f.close()

clock_display = ClockDisplay(text_color=CONFIG_DATA["time_color"])
clock_display.x = 44
clock_display.y = 22

playlist_display = PlaylistDisplay(text_color=CONFIG_DATA["text_color"])
playlist_display.x = 13
playlist_display.y = 234

playlist_display.from_files_list(PLAYLIST["playlist"]["files"])
playlist_display.current_track_number = 11


current_song_lbl = ScrollingLabel(terminalio.FONT, full_text=playlist_display.current_track_title,
                                  color=CONFIG_DATA["text_color"], max_characters=22)
current_song_lbl.anchor_point = (0, 0)
current_song_lbl.anchored_position = (98, 19)


# Setup the file as the bitmap data source
bitmap = displayio.OnDiskBitmap(SKIN_IMAGE)

# Create a TileGrid to hold the bitmap
background_tilegrid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

# Create a Group to hold the TileGrid
main_group = displayio.Group()

# Add the TileGrid to the Group
main_group.append(background_tilegrid)

main_group.append(current_song_lbl)
main_group.append(clock_display)
main_group.append(playlist_display)

# Add the Group to the Display
display.show(main_group)

# print((display.width, display.height))


_start_time = time.monotonic()

while True:
    _cur_time = time.monotonic()
    _seconds_elapsed = _cur_time - _start_time
    # print(_seconds_elapsed)
    clock_display.seconds = int(_seconds_elapsed)

    current_song_lbl.update()
