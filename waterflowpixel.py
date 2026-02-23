import time
from neopixel import Neopixel

class WaterflowPixel:
    
    def __init__(self, num_leds, state_machine, pin, mode="BRG", delay=0.0003):
        """
        Constructor for library class
        :param num_leds:  number of leds on your led-strip
        :param state_machine: id of PIO state machine used
        :param pin: pin on which data line to led-strip is connected
        :param mode: [default: "RGB"] mode and order of bits representing the color value.
        This can be any order of RGB or RGBW (neopixels are usually GRB)
        :param delay: [default: 0.0003] delay used for latching of leds when sending data
        """
        self.pin = pin
        self.strip = Neopixel(num_leds, state_machine, pin, mode, delay)
        self.constParam = [state_machine, pin, mode, delay]
        self.pixels = 0
        self.strip.clear()
        self.strip.fill((0,0,0))
        self.strip.show()
        
    def __repr__(self):
        return f'WaterflowPixel(GPIO{self.pin}, num_leds={self.strip.num_leds}, state_machine={self.strip.sm})'
    
    def showAndWait(self, s=0):
        """
        Send data to led-strip, making all changes on leds have an effect.
        This method should be used after every method that changes the state of leds or after a chain of changes.
        After that it waits specified time
        :param s: waiting time in seconds
        :return: None
        """
        num = 1
        if (s > self.strip.delay):
            add = s / (self.strip.delay * self.strip.num_leds)
            num += add
        for x in range(num):
            self.strip.show()
            
    def addPixel(self, color=(255, 255, 255), overflow=False):
        if (color is None):
            color = (0,0,0)
        if (self.pixels < self.strip.num_leds or overflow):
            self.strip.set_pixel(-1, color)
            if (self.pixels < self.strip.num_leds):
                self.pixels += 1
            self.strip.rotate_right()
        
    def removePixel(self):
        if (self.pixels > 0):
            self.strip.set_pixel(0, (0, 0, 0), 0)
            self.strip.rotate_left()
            self.pixels -= 1
        
    def removeAll(self):
        self.strip.clear()
        self.strip.fill((0, 0, 0), 0)
        
    def getBrightness(self, color=(255,255,255)):
        return max(color)
    
    def setBrightness(self, pixelIndex, brightness=255):
        if (pixelIndex is None):
            self.strip.brightness(brightness)
        else:
            if (brightness > 255):
                self.setBrightness(pixelIndex)
            else:
                color = self.strip.get_pixel(pixelIndex)
                br = self.getBrightness(color)
                print(br)
                r = color[0] + 255 - br
                g = color[1] + 255 - br
                b = color[2] + 255 - br
                color = (r, g, b)
                print(self.getBrightness(color))
                self.strip.set_pixel(pixelIndex, color, brightness)
            
    def setNumberOfLEDs(self, nol):
        if (nol != self.strip.num_leds):
            print("setting the number of LEDs:" + str(nol))
            self.strip = Neopixel(nol, self.constParam[0], self.constParam[1], self.constParam[2], self.constParam[3])
            self.removeAll()
            