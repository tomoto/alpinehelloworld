from __future__ import division
import sys
import logging
import cv2
import numpy as np
import colorsys
# import matplotlib
# import matplotlib.pyplot as plt

class Level:

    def __new__(cls):
        _value_ = "level"

    def __init__(self, level, hue, required_xp, next):
        self.level = level
        self.hue = hue
        self.required_xp = required_xp
        self.next = next

    def __repr__(self):
        return str(self.level)

Level.GOLD = Level(3, 26, 30000, None)
Level.SILVER = Level(2, 98, 4000, Level.GOLD)
Level.BRONZE = Level(1, 14, 500, Level.SILVER)
Level.NONE = Level(0, 55, 0, Level.BRONZE)

logging.basicConfig(level=logging.DEBUG)

# Screen metrics at width 1080
SCREEN_WIDTH = 1080
FULL_BAR_WIDTH = 136

def dimension(img):
    return (len(img[0]), len(img))

def hsv2bgr(h, s, v):
    # too complicated, I hate this
    return (cv2.cvtColor(np.array([[[h, s, v]]], np.uint8), cv2.COLOR_HSV2BGR)[0][0]).astype(np.int)

def compare(a, b, eps):
    return abs(a - b) <= eps

def calc_remaining_xp(bar_width, badge_level):
    return max((1.0 - bar_width / FULL_BAR_WIDTH) * badge_level.next.required_xp, 0)

def determine_badge_level(hsv_img, bar_rect):
    delta_x, delta_y = (88, -8)
    hsv = hsv_img[bar_rect[1] + delta_y][bar_rect[0] + delta_x]
    logging.debug("Badge color: %s", hsv)
    for level in (Level.SILVER, Level.BRONZE, Level.NONE):
        if compare(hsv[0], level.hue, 3):
            return level
    return None

def validate_bar_position(bar_rect):
    if bar_rect[0] < SCREEN_WIDTH - FULL_BAR_WIDTH:
        for possible_bar_x in range(115, SCREEN_WIDTH - FULL_BAR_WIDTH, 345):
            if compare(bar_rect[0], possible_bar_x, 3):
                return True
    return False

def validate_bar_size(bar_rect):
    return compare(bar_rect[3], 10, 3)

def find_bar_rects(bar_img):
    _, contours, hierarcy = cv2.findContours(bar_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boundingRect(c) for c in contours]

def extract_bar_img(hsv_img):
    lower_color = np.array([80, 180, 0])
    upper_color = np.array([90, 255, 255])
    return cv2.inRange(hsv_img, lower_color, upper_color)

def draw_xp_text(img, rect, xp, fg_color, bg_color):
    font_face = cv2.FONT_HERSHEY_DUPLEX
    font_size = 1.25
    font_thickness = 3
    text = str(int(xp))
    text_size = cv2.getTextSize(text, font_face, font_size, font_thickness)
    text_offset = 5
    text_margin = 5
    cv2.rectangle(img,
                  (rect[0], rect[1] - text_offset - text_size[0][1] - text_margin * 2),
                  (rect[0] + FULL_BAR_WIDTH, rect[1] - text_offset),
                  bg_color, -1)
    cv2.putText(img, text,
                (rect[0] + FULL_BAR_WIDTH - text_size[0][0], rect[1] - text_offset - text_margin),
                font_face, font_size, fg_color, font_thickness, cv2.LINE_AA)

def process_image_data_raw(orig_img):
    orig_width, _ = dimension(orig_img)
    if orig_width != SCREEN_WIDTH:
        r = SCREEN_WIDTH / orig_width
        orig_img = cv2.resize(orig_img, None, fx=r, fy=r, interpolation=cv2.INTER_NEAREST)

    hsv_img = cv2.cvtColor(orig_img, cv2.COLOR_BGR2HSV)

    bar_img = extract_bar_img(hsv_img)

    bar_rects = find_bar_rects(bar_img)

    result_img = np.copy(orig_img)

    for rect in bar_rects:
        logging.debug("Bounding rect: %s", rect)
        if not (validate_bar_size(rect) and validate_bar_position(rect)):
            continue
        badge_level = determine_badge_level(hsv_img, rect)
        logging.debug("Badge level: %s", badge_level)
        if badge_level == None:
            continue
        remaining_xp = calc_remaining_xp(rect[2], badge_level)
        logging.debug("Remaining XP: %s", remaining_xp)
        bg_color = hsv2bgr(badge_level.next.hue, 120, 240)
        draw_xp_text(result_img, rect, remaining_xp, (0, 0, 0), bg_color)

    return result_img, bar_img

def process_image_data(data, extension):
    npdata = np.fromstring(data, np.uint8)
    orig_img = cv2.imdecode(npdata, cv2.IMREAD_COLOR)
    result_img, _ = process_image_data_raw(orig_img)
    _, buf = cv2.imencode(extension, result_img)
    return buf.tobytes()
