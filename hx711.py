from machine import Pin
import time

class HX711:
    def __init__(self, dout_pin, sck_pin):
        self.pOUT = Pin(dout_pin, Pin.IN)
        self.pSCK = Pin(sck_pin, Pin.OUT)
        self.pSCK.value(0)

    def read(self):
        for _ in range(500):
            if self.pOUT.value() == 0:
                break
            time.sleep_ms(1)
        else:
            return 0 
        
        data = 0
        for _ in range(24):
            self.pSCK.value(1)
            data = (data << 1) | self.pOUT.value()
            self.pSCK.value(0)
            
        self.pSCK.value(1)
        self.pSCK.value(0)
        
        if data & 0x800000:
            data -= 0x1000000
        return data