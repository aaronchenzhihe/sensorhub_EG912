import utime
from machine import I2C
from usr.libs import CurrentApp
from usr.libs.threading import Thread
from usr.libs.logging import getLogger
from usr.drivers.shtc3 import Shtc3, SHTC3_SLAVE_ADDR
from usr.drivers.lps22hb import Lps22hb, LPS22HB_SLAVE_ADDRESS
from usr.drivers.tcs34725 import Tcs34725, TCS34725_SLAVE_ADDR
from usr.drivers.icm20948 import ICM20948, I2C_ADD_ICM20948



logger = getLogger(__name__)


class SensorService(object):

    def __init__(self, app=None):
        # i2c channel 0 
        self.i2c_channel0 = I2C(I2C.I2C1, I2C.STANDARD_MODE)
        # SHTC3
        self.shtc3 = Shtc3(self.i2c_channel0, SHTC3_SLAVE_ADDR)
        self.shtc3.init()
        # LPS22HB
        self.lps22hb = Lps22hb(self.i2c_channel0, LPS22HB_SLAVE_ADDRESS)
        self.lps22hb.init()
        # TCS34725
        self.tcs34725 = Tcs34725(self.i2c_channel0, TCS34725_SLAVE_ADDR)
        self.tcs34725.init()
        #ICM20948
        self.icm20948 = ICM20948(self.i2c_channel0)

        print('\nSENSOR\n')

        if app is not None:
            self.init_app(app)

    def __str__(self):
        return '{}'.format(type(self).__name__)

    def init_app(self, app):
        app.register('sensor_service', self)

    def load(self):
        logger.info('loading {} extension, init sensors will take some seconds'.format(self))
        Thread(target=self.start_update).start()


    def get_temp1_and_humi(self):
        return self.shtc3.getTempAndHumi()
    
    def get_press_and_temp2(self):
        return self.lps22hb.getTempAndPressure()
    
    def get_rgb888(self):
            rgb888 = self.tcs34725.getRGBValue()
            logger.debug("R: {}, G: {}, B: {}".format((rgb888 >> 16) & 0xFF, (rgb888 >> 8) & 0xFF, rgb888 & 0xFF))

            r = (rgb888 >> 16) & 0xFF
            g = (rgb888 >> 8) & 0xFF
            b = rgb888 & 0xFF
            return r, g, b       
    
    def get_accel_gyro(self):
        return self.icm20948.icm20948_Gyro_Accel_Read()

    def start_update(self):
        prev_temp1 = None
        prev_humi = None
        prev_press = None
        prev_temp2 = None
        prev_rgb888 = None
        prev_accel =None
        prev_gyro = None


        while True:
            data = {}

            try:
                accel, gyro = self.get_accel_gyro()           
                print('\r\nGyroscope:     X = %d , Y = %d , Z = %d\r\n'%(gyro[0],gyro[1],gyro[2]))
                print('\r\nAcceleration:  X = %d , Y = %d , Z = %d\r\n'%(accel[0],accel[1],accel[2]))
                if prev_accel is None or abs(prev_accel[0] - accel[0]) + abs(prev_accel[1] - accel[1]) + abs(prev_accel[2] - accel[2]) > 400:
                    data.update({10: {1: accel[0], 2: accel[1], 3: accel[2]}})
                    prev_accel = [0, 0, 0]
                    prev_accel[0] = accel[0]
                    prev_accel[1] = accel[1]
                    prev_accel[2] = accel[2]
                if prev_gyro is None or abs(prev_gyro[0] - gyro[0]) + abs(prev_gyro[1] - gyro[1]) + abs(prev_gyro[2] - gyro[2]) >= 10:
                    data.update({9: {1: gyro[0], 2: gyro[1], 3: gyro[2]}})
                    prev_gyro = [0, 0, 0]
                    prev_gyro[0] = gyro[0]
                    prev_gyro[1] = gyro[1]
                    prev_gyro[2] = gyro[2]
            except Exception as e:
                logger.error("getAccelGyro error:{}".format(e))

            utime.sleep_ms(100)

            try:
                temp1, humi = self.shtc3.getTempAndHumi()
                logger.debug("temp1: {:0.2f}, humi: {:0.2f}".format(temp1, humi))

                if prev_temp1 is None or abs(prev_temp1 - temp1) > 1:
                    data.update({3: round(temp1, 2)})
                    prev_temp1 = temp1

                if prev_humi is None or abs(prev_humi - humi) > 1:
                    data.update({4: round(humi, 2)})
                    prev_humi = humi

            except Exception as e:
                logger.error("getTempAndHumi error:{}".format(e))

            utime.sleep_ms(100)

            try:
                press, temp2 = self.lps22hb.getTempAndPressure()
                logger.debug("press: {:0.2f}, temp2: {:0.2f}".format(press, temp2))

                if prev_temp2 is None or abs(prev_temp2 - temp2) > 1:
                    data.update({5: round(temp2, 2)})
                    prev_temp2 = temp2

                if prev_press is None or abs(prev_press - press) > 1:
                    data.update({6: round(press, 2)})
                    prev_press = press

            except Exception as e:
                logger.error("getTempAndPressure error:{}".format(e))

            utime.sleep_ms(100)

            try:
                rgb888 = self.tcs34725.getRGBValue()
                logger.debug("R: {}, G: {}, B: {}".format((rgb888 >> 16) & 0xFF, (rgb888 >> 8) & 0xFF, rgb888 & 0xFF))

                r = (rgb888 >> 16) & 0xFF
                g = (rgb888 >> 8) & 0xFF
                b = rgb888 & 0xFF

                if prev_rgb888 is None:
                    data.update({7: {1: r, 2: g, 3: b}})
                    prev_rgb888 = rgb888
                else:
                    prev_r = (prev_rgb888 >> 16) & 0xFF
                    dr = abs(r - prev_r)
                    
                    prev_g = (prev_rgb888 >> 8) & 0xFF
                    dg = abs(g - prev_g)
                    
                    prev_b = prev_rgb888 & 0xFF
                    db = abs(b - prev_b)

                    # 色差超过 200 即认为颜色有变化
                    if pow(sum((dr*dr, dg*dg, db*db)), 0.5) >= 200:
                        data.update({7: {1: r, 2: g, 3: b}})
                        prev_rgb888 = rgb888

            except Exception as e:
                logger.error("getRGBValue error:{}".format(e))

            if data:
                with CurrentApp().qth_client:
                    for _ in range(3):
                        if CurrentApp().qth_client.sendTsl(1, data):
                            break
                        else:
                            prev_temp1 = None
                            prev_humi = None
                            prev_press = None
                            prev_temp2 = None
                            prev_rgb888 = None
                            prev_rgb888 = None
                            prev_accel =None    

            utime.sleep(1)
