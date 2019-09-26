#!/usr/bin/env python
######################################################################################################
# 02ag  only PC
# 02b   for RPi
# 02c   Edit on RPi,
# 02d   LED on when checking, check Length of Redis value and loop, PWS GUI
# 02e   Redis on PWS

import time
import datetime
print  (datetime.datetime.now()).strftime("%m/%d %H:%M:%S") + " ******************************"
import RPi.GPIO as GPIO
import smbus            # I2C         
import os               # os.environ['XX_KEY']
import redis            # Redis
# import boto3          # AWS   slowWWWWWWWWWWWWWWWWWWWWWWWWWWWWW ->import _main_
print  (datetime.datetime.now()).strftime("%m/%d %H:%M:%S")
import pygame.mixer     # voice
from password import *  # for pw .ignore

### switch ###
Redis_type = 1          # 0:local , 1:Remote
Check_type = 1          # 0:Check elements, 1:Compare reference

# global r              ###################################### check
InSetPin = 16           # pin16 --- Input Set button
InChkPin = 18           # pin18 --- Input Chk button
OutLightPin = 13        # pin13 --- Output Light  
OutChkPin = 15          # pin15 --- Output led Chk

### bus = smbus.SMBus(1)                                # Init I2C
addr = 0x2a                                             # S11059-02DT Addr for I2C
# param=[0x00,0x08,0x091,0x09,0x02,0x03,0x0a,0x0b]      # Sencitivity for Sensor
Sense_Time = 0.6                                        # Integration time
Sense_limit = 50                                        # for brihgt env : Allowable Sence margin limit
# Sense_limit = 20                                      # for dark env : Allowable margin limit
Color_limit = 350                                       # for brihgt env : Allowable margin limit
Color_margin = 0.4                                      # compare margin = 40 %

region_name = "us-east-1"
     
###### 1cm with light
#Red = [5000, 1500, 1000, 400]                          # refernce for Red
#Gre = [2000, 9000, 3000, 300]                          # refernce for Green
#Blu = [1000, 3300, 5500, 190]                          # refernce for Blue

###### put Radis
# print "put Redis"
## Colors_set = ['Red', 'Gre', 'Blu']
## for f in Colors_set:
#for i in range(3):
#        print i
#        r.rpush('Red', Red[i])  # put color datas
#        r.rpush('Gre', Gre[i])  # put color datas
#        r.rpush('Blu', Blu[i])  # put color datas
#        r.rpush('Unk', Blu[i])  # put color datas

#####################
#mp3_name = "Unknown.mp3"
#print "Make:" + mp3_name
#talk_to_me = "I don't know!!"
#polly = boto3.client('polly', region_name='us-west-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
#response = polly.synthesize_speech(
#        OutputFormat='mp3', Text=talk_to_me, TextType='text', VoiceId='Joanna')
#with open(mp3_name , 'wb') as f:
#        f.write(response['AudioStream'].read())
#####################

def InitColor(DB_location):                ############ Get color data from Redis ######################################
        global r
        global Ref_Red
        global Ref_Gre
        global Ref_Blu
        global Ref_Ukn
        if DB_location == 0:
                #Local_DB = "127.0.0.1"
                #Local_DB = "192.168.0.34"
                Local_DB = "172.20.10.3"
                print "0: local Redis " + Local_DB
                r = redis.Redis(host=Local_DB, port='6379', db=1)
        else:
                print "1: Remote Redis " + REDIS_HOST
        Ref_Red = GetColorDB("Red")
        #print Ref_Red
        Ref_Gre = GetColorDB("Gre")
        Ref_Blu = GetColorDB("Blu")
        Ref_Ukn = GetColorDB("Unk")

def PutColorDB(db_key, lst_data):
        global r
        print "PutColorDB(db_key, lst_data):"
        print db_key
        print lst_data
        for i in range(3):
                r.rpush(db_key, lst_data[i])  # put color datas

def GetColorDB(db_key):
        global r
        print "GetColorDB(" + db_key + ") len:" + str(r.llen(db_key))
        ret = []
        for i in range(3):
                dat = int(r.lindex(db_key, i))
                ret.append(dat)
        print ret
        return ret

def InitGPIO():
        GPIO.setmode(GPIO.BOARD)                                # Numbers GPIOs by physical location
        GPIO.setwarnings(False)
        GPIO.setup(OutLightPin, GPIO.OUT)                       # Set Pin's mode Output
        GPIO.setup(InSetPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set Pin's modeIinput, Pull up 3.3V
        GPIO.output(OutLightPin, GPIO.LOW)                      # LightPin low to LED off

        GPIO.setup(OutChkPin, GPIO.OUT)                         # Set Pin's mode Output
        GPIO.setup(InChkPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set Pin's mode Input, Pull up 3.3V
        GPIO.output(OutChkPin, GPIO.HIGH)                       # Chk Rdy LED ON

def SenseColor():
        global bus
        print "call SenseColor"
        ### Light ON
        GPIO.output(OutLightPin, GPIO.HIGH)                     # Light led on
        
        bus = smbus.SMBus(1)                                    # Init I2C
        time.sleep(0.1)                                         # Setting time margin
        bus.write_byte_data(addr , 0x00, 0x80)                  # Init Sensor
        time.sleep(0.1)                                         # Setting time margin
        bus.write_byte_data(addr , 0x00, 0x0b)                  # Set Sensor sensitivity
        # time.sleep(Sense_Time)                                  # Setting time margin
        ret_RGB = [0, 0, 0]
        for i in range(10):
                time.sleep(Sense_Time)
                data = bus.read_i2c_block_data(addr , 0x03, 8) 
                R = data[0] *256 + data[1]
                G = data[2] *256 + data[3]
                B = data[4] *256 + data[5]
                print (R, G, B)
                time.sleep(Sense_Time)
                data2 = bus.read_i2c_block_data(addr , 0x03, 8) 
                R2 = data2[0] *256 + data2[1]
                G2 = data2[2] *256 + data2[3]
                B2 = data2[4] *256 + data2[5]
                print (R2, G2, B2)
                if abs(R - R2) < Sense_limit and abs(G - G2) < Sense_limit and abs(B - B2) < Sense_limit:  # when stable val then break
                        ret_RGB = [R, G, B]
                        break
        ### Light OFF
        GPIO.output(OutLightPin, GPIO.LOW)                      # Light led off
        return ret_RGB

def CompareColor(ret_col):
        print "call CompareColor"
        print "Ref Red:" + str(Ref_Red)
        print "Ref Gre:" + str(Ref_Gre)
        print "Ref Blu:" + str(Ref_Blu)
        Red_limit = ret_col[0] * Color_margin                   ### margin 20 %
        Gre_limit = ret_col[1] * Color_margin                   ### margin 20 %        
        Blu_limit = ret_col[2] * Color_margin                   ### margin 20 %
        ret_txt = "Unknown"
        
        # check RED?
        if abs(ret_col[0] - Ref_Red[0]) < Red_limit and abs(ret_col[1] - Ref_Red[1]) < Gre_limit and abs(ret_col[2] - Ref_Red[2]) < Blu_limit:  
                ret_txt = "Red"
        # check Green?
        elif abs(ret_col[0] - Ref_Gre[0]) < Red_limit and abs(ret_col[1] - Ref_Gre[1]) < Gre_limit and abs(ret_col[2] - Ref_Gre[2]) < Blu_limit:
                ret_txt = "Green"
        # check Blue?
        elif abs(ret_col[0] - Ref_Blu[0]) < Red_limit and abs(ret_col[1] - Ref_Blu[1]) < Gre_limit and abs(ret_col[2] - Ref_Blu[2]) < Blu_limit: 
                ret_txt = "Blue"
        return ret_txt

def JudgeColor(ret_col):
        print "call JudgeColor"
        if ret_col[0] > ret_col[1]:
                if ret_col[0] > (ret_col[2] * 2):   # check RED?
                        ret_txt = "Red"
                else:
                        ret_txt = "Blue"
        else:
                if ret_col[1] > (ret_col[2] * 1.5):   # Dark room /// check Green?
                        ret_txt = "Green"
                else:
                        ret_txt = "Blue"
        return ret_txt
                                
def TalkMsg(mp3_name):
        mp3_name = mp3_name + ".mp3"
        print "Talk:" + mp3_name
        pygame.mixer.init()
        pygame.mixer.music.load(mp3_name)
        time.sleep(1)
        pygame.mixer.music.play()
        time.sleep(3)
        pygame.mixer.music.stop()

def TalkColor(color_txt):
        mp3_name = color_txt + ".mp3"
        print "call TalkColor:" + mp3_name
        if not os.path.exists("./" + mp3_name):
                talk_to_me = "This color is" + color_txt
                polly = boto3.client('polly', region_name='us-west-2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

                response = polly.synthesize_speech(
                        OutputFormat='mp3',
                        Text=talk_to_me,
                        TextType='text',
                        VoiceId='Joanna')
                with open(mp3_name , 'wb') as f:
                        f.write(response['AudioStream'].read())
        ### call TalkMsg ###
        TalkMsg(color_txt)                

def mainloop():
        while True:
                ### Set color (Not Use...) ###########################
                if GPIO.input(InSetPin) == GPIO.LOW: ### Set button is pressed or not.
                        print '...Set led on'
                        # GPIO.output(OutLightPin, GPIO.LOW)  # Set led on
                        # Set color ###

                        
                        # GPIO.output(OutLightPin, GPIO.HIGH) # Set led off         
                #else:
                        # print 'Set led off...'
                        # GPIO.output(OutLightPin, GPIO.HIGH) # Set led off
                        
                ### Sense color ################################
                if GPIO.input(InChkPin) == GPIO.LOW:            ### Chk button is pressed or not.
                        print  (datetime.datetime.now()).strftime("%m/%d %H:%M:%S")
                        print 'Cheking...'
                        GPIO.output(OutChkPin, GPIO.LOW)        # Chk Rdy led OFF
                        ### Chk color ###
                        ret_col = SenseColor()                  ################# return [R,G,B]
                        if ret_col[0] == 0:
                                ret_result = "Unstable"
                        elif Check_type == 0:
                                ret_result = JudgeColor(ret_col)        ### return only RGB Color text
                        else:
                                ret_result = CompareColor(ret_col)     ### return Color text
                                
                        print "Color = " + ret_result
                        TalkColor(ret_result)                   # Talk msg
                        
                        if ret_result <> "Unstable":
                                PutColorDB(ret_result[:3], ret_col) # Put Color Data to DB
                GPIO.output(OutChkPin,GPIO.HIGH)       # Chk Rdy led ON

def destroy():
        global bus
        bus.write_byte_data(addr, 0x00, 0x80)   # Init Sensor
        GPIO.cleanup()                          # Release resource

if __name__ == '__main__':                      ### start here #######################
        global bus
        print  (datetime.datetime.now()).strftime("%m/%d %H:%M:%S")
        TalkMsg("start")                        # talk Hello 
        import boto3                            # AWS   slowWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
        InitColor(Redis_type)                   # Redis (0 local, 1 remote)
        InitGPIO()                              # Init GPIO
        if Check_type == 0:
                print "0:JudgeColor(ret_col)"   ### return only RGB Color text
        else:
                print "1:CompareColor(ret_col)" ### return Color text
        TalkMsg("usage")                        # talk Usage
        try:
                print "main loop"
                mainloop()                      # main loop
        except KeyboardInterrupt:               # When 'Ctrl+C' is pressed, Execute destroy() 
                TalkMsg("bye")
                destroy()
        except IOError as e:
                TalkMsg("sorry")
                print("type:{0}".format(type(e)))
                print("args:{0}".format(e.args))
                print("message:{0}".format(e.message))
                print("{0}".format(e))                
                destroy()
################################################ end ###############################################
