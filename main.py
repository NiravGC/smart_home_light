# NOTES ON CONFIGURATION
# Strip is made up of three controllable sections; left, middle, and bar.
# LEFT section is the first 24 pixels
# MIDDLE section is pixels 25 - 74
# BAR section is pixels 75 - 132

import time
import logging
import os

from flask import Flask
from flask_ask import Ask, request, session, question, statement
import RPi.GPIO as GPIO

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

# Import the WS2801 module.
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

# Number of LEDs in strip:
PIXEL_COUNT = 133

# Currently assigned colour
LEFT_COLOUR = "white"
MIDDLE_COLOUR = "white"
BAR_COLOUR = "white"

# Specify a hardware SPI connection on /dev/spidev0.0:
SPI_PORT   = 0
SPI_DEVICE = 0
pixels = Adafruit_WS2801.WS2801Pixels(PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

# ================================ #
#      DEFINE LIGHT FUNCTIONS      #
# ================================ #

# Change section to single colour
def single_colour(first, last, r, g, b):
  for i in range(first, last):          # defined start and end pixels to change
    pixels.set_pixel_rgb(i, r, g, b)
    pixels.show()                       # show to update pixels
    
# Get values for dimming
def dimvalues(lcn, amt):
      val = int(amt)
      r,g,b = colourdict[lcn][0], colourdict[lcn][2], colourdict[lcn][1]  # take colour values - again accounting for the rbg change
      rvalue = r*val/100  # adjust by % based on given value 1-100
      gvalue = g*val/100
      bvalue = b*val/100
      return rvalue, gvalue, bvalue
    
# ================================ #
#    DICTIONARIES FOR COMMANDS     #
# ================================ #

# select first and last pixels in section
locationdict = {
  "left": [0, 24],
  "middle": [24, 74],
  "bar": [74, PIXEL_COUNT],
  "living room": [0, PIXEL_COUNT]
}

# assign RGB values based on colour name
colourdict = {
  "red": [255, 0, 0],
  "green": [0, 255, 0],
  "blue": [0, 0, 255],
  "orange": [255, 110, 0],
  "yellow": [255, 255, 0],
  "forest": [50, 160, 0],
  "teal": [20, 160, 150],
  "light blue": [0, 255, 255],
  "purple": [150, 0, 255],
  "pink": [255, 0, 255],
  "white": [255, 255, 255],
}


# ================================ #
#       ALEXA FUNCTIONALITY        #
# ================================ #
  
@ask.launch
def launch():
    speech_text = 'Novello Smart Lighting Online'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)

  
# amazon intent for changing specific section to a given colour
@ask.intent('SetColourIntent', default = {'Location':'Living Room'})
def SetColourIntent(Location, Colour):
    if Location in locationdict and Colour in colourdict:
      rvalue = colourdict[Colour][0]
      gvalue = colourdict[Colour][2]          # has become RBG for some reason? This fixes
      bvalue = colourdict[Colour][1]
      firstpixel = locationdict[Location][0]
      lastpixel = locationdict[Location][1]
      single_colour(firstpixel, lastpixel, rvalue, gvalue, bvalue)
      if Location == "left":
        LEFT_COLOUR = Colour
      elif Location == "middle":
        MIDDLE_COLOUR = Colour
      elif Location == "bar":
        BAR_COLOUR = Colour
      else:
        LEFT_COLOUR = MIDDLE_COLOUR = BAR_COLOUR = Colour
      return statement('colouring {} lights {}'.format(Location, Colour))
    elif Location not in locationdict:
      return statement('I do not know which lights you want changed.')
    else:
      return statement('I do not have that colour saved.')

    
# amazon intent for turning off specific lights
@ask.intent('ClearIntent', default = {'Location':'Living Room'})
def ClearIntent(Location):
    if Location in locationdict:
      firstpixel = locationdict[Location][0]
      lastpixel = locationdict[Location][1]
      for i in range(firstpixel, lastpixel):
        pixels.set_pixel(i, 0)
      pixels.show()
      return statement('Turning off {} lights'.format(Location))
    else:
      return statement('I do not know which lights you want changed.')
    
    
# amazon intent for dimming specific lights
@ask.intent('DimIntent', default = {'Location':'Living Room'})
def DimIntent(Location, Value):
    if Location in locationdict and 0 < int(Value) <= 100:
      if Location == "left":
        firstpixel = locationdict[Location][0]
        lastpixel = locationdict[Location][1]
        dimvalues(LEFT_COLOUR, Value)
        single_colour(firstpixel, lastpixel, rvalue, gvalue, bvalue)
      elif Location == "middle":
        firstpixel = locationdict[Location][0]
        lastpixel = locationdict[Location][1]
        dimvalues(MIDDLE_COLOUR, Value)
        single_colour(firstpixel, lastpixel, rvalue, gvalue, bvalue)
      elif Location == "bar":
        firstpixel = locationdict[Location][0]
        lastpixel = locationdict[Location][1]
        dimvalues(BAR_COLOUR, Value)
        single_colour(firstpixel, lastpixel, rvalue, gvalue, bvalue)
      else:
        for l, c in zip(("left", "middle", "bar"), (LEFT_COLOUR, MIDDLE_COLOUR, BAR_COLOUR)):
          firstpixel = locationdict[l][0]
          lastpixel = locationdict[l][1]
          dimvalues(c, Value)
          single_colour(firstpixel, lastpixel, rvalue, gvalue, bvalue)
    elif Location not in locationdict:
      return statement('I do not know which lights you want changed.')
    else:
      return statement('Please use a value between zero and one-hundred')
    
      

@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'You can say hello to me!'
    return question(speech_text).reprompt(speech_text).simple_card('HelloWorld', speech_text)

@ask.session_ended
def session_ended():
    return "{}", 200

 
# run mainloop 
if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)
