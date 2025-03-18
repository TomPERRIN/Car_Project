import RPi.GPIO as GPIO
from time import sleep
from vosk import Model, KaldiRecognizer
import pyaudio

#---------------Import du modèle de reconnaissance vocale---------------#
model = Model(r"/home/tompe/Project/vosk-model-small-fr-0.22")
recognizer = KaldiRecognizer(model, 16000)

mic = pyaudio.PyAudio()
#parametres par défaut : pyaudio.paInt16, 1, 16000, True, 8192
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=18000, input=True, frames_per_buffer=8192)
stream.start_stream()

#------------------Definition et configuration des pins-----------------#

#Pins du moteur 1
M1_En = 21
M1_In1 = 16
M1_In2 = 20
#Pins du moteur 2
M2_En = 18
M2_In1 = 23
M2_In2 = 24

Pins = [[M1_En, M1_In1, M1_In2], [M2_En, M2_In1, M2_In2]]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Configuration des pins en sortie
GPIO.setup(M1_En, GPIO.OUT)
GPIO.setup(M1_In1, GPIO.OUT)
GPIO.setup(M1_In2, GPIO.OUT)

GPIO.setup(M2_En, GPIO.OUT)
GPIO.setup(M2_In1, GPIO.OUT)
GPIO.setup(M2_In2, GPIO.OUT)

#Reglage de la vitesse de base pour les 2 moteurs
M1_Vitesse = GPIO.PWM(M1_En, 100)
M2_Vitesse = GPIO.PWM(M2_En, 100)
Vitesse1 = 50
Vitesse2 = 50
M1_Vitesse.start(Vitesse1)
M2_Vitesse.start(Vitesse2)


#------------Faire tourner dans le sens 1 le moteur souhaité------------#
# Moteur 1 avance                                                       #
# Moteur 2 tourne à droite                                              #
#-----------------------------------------------------------------------#
def sens1(moteurNum) :
    GPIO.output(Pins[moteurNum - 1][1], GPIO.HIGH)
    GPIO.output(Pins[moteurNum - 1][2], GPIO.LOW)

#------------Faire tourner dans le sens 2 le moteur souhaité------------#
# Moteur 1 recule                                                       #
# Moteur 2 tourne à gauche                                              #
#-----------------------------------------------------------------------#
def sens2(moteurNum) :
    GPIO.output(Pins[moteurNum - 1][1], GPIO.LOW)
    GPIO.output(Pins[moteurNum - 1][2], GPIO.HIGH)

#------------------------Arrêt du moteur souhaité-----------------------#
# Arrête le moteur passé en paramètre                                   #
#-----------------------------------------------------------------------#
def arret(moteurNum) :
    GPIO.output(Pins[moteurNum - 1][1], GPIO.LOW)
    GPIO.output(Pins[moteurNum - 1][2], GPIO.LOW)

#--------------------------Arrêt des 2 moteurs--------------------------#
# Veut bien dire ce que ça veut dire                                    #
#-----------------------------------------------------------------------#
def arretComplet() :
    GPIO.output(Pins[0][1], GPIO.LOW)
    GPIO.output(Pins[0][2], GPIO.LOW)
    GPIO.output(Pins[1][1], GPIO.LOW)
    GPIO.output(Pins[1][2], GPIO.LOW)

#----------------------------Avancer/Reculer----------------------------#
# Paramètres : Instructions, état de mobilité                           #
# Sortie     : Etat de mobilité                                         #
# -Suit les instructions pour avancer ou reculer                        #
# -Retourne l'état de mobilité de la voiture                            #
#-----------------------------------------------------------------------#
def avancer(text, bouge):
    move = False
    if not(bouge):
        Vitesse1 = 30
        M1_Vitesse.start(Vitesse1)
    if "avan" in text or "accè" in text or "accé" in text:
        sens1(1)
        move = True
    #reculer
    elif "recul" in text:
        sens2(1)
        move = True
    return move

#---------------------------Accélérer/Ralentir--------------------------#
# Paramètres : Instructions, état de mobilité                           #
# Sortie     : Accélération ou ralentissement à effectuer               #
# -Suit les instructions pour accélérer ou ralentir                     #
#-----------------------------------------------------------------------#
def acc_ral (text, bouge):
    acceleration = 0
    if bouge :
        if "accé" in text or "accè" in text or "avan" in text:
            if "max" in text or "box" in text or "fon" in text:
                acceleration = 10
            elif "for" in text or "beau" in text:
                acceleration = 1
            else :
                acceleration = 0.5
        if "ralenti" in text:
            if "max" in text or "mini" in text or "box" in text or "fon" in text:
                acceleration = -10
            elif "for" in text or "beau" in text:
                if Vitesse1 > 70:
                    acceleration = -4
                else:
                    acceleration = -2
            else :
                acceleration = -1
    return acceleration
    
#------------------------------Acceleration-----------------------------#
# Paramètre  : vitesse de base, accélération voulue                     #
# Sortie     : Les instructions suivies                                 #
# id_acceleration = [-10, -4, -2, -1, 0, 0.5, 1, 10]                   #
# -Applique l'accélération souhaité                                     #
# -Retourne les instructions correspondantes                            #
#-----------------------------------------------------------------------#   
def accelerer(vitesse, acceleration) :
    instr = ""
    match acceleration:
        case -4 | -2 :
            instr = "ralenti fort"
        case -1 :
            instr = "ralenti"
        case 0.5 :
            instr = "accélère"
        case 1 :
            instr = "accélère fort"
        case -10 :
            instr = "ralenti max"
        case 10 :
            instr = "accélère max"
    vitesse = vitesse + acceleration*10
    #La vitesse doit être comprise entre 10 et 80
    if vitesse < 10:
        vitesse = 10
    elif vitesse > 100:
        vitesse = 80
    
    M1_Vitesse.start(vitesse)
    return vitesse, instr
    
#--------------------------------Tourner--------------------------------#
# Paramètre : Instructions                                              #
# Sortie    : Les instructions suivies                                  #
# -Fait tourner dans le sens souhaité                                   #
# -Retourne l'instruction correspondante                                #
#-----------------------------------------------------------------------#
def tourner (text):
    instr = ""
    if "droite" in text:
        sens1(2)
        sleep(1)
        arret(2)
        instr = "droite"
    elif "gauche" in text:
        sens2(2)
        sleep(1)
        arret(2)
        instr = "gauche"
    return instr
    
#---------------------------------Couper--------------------------------#
# Paramètres : Instructions, état de mobilité                           #
# Sortie     : Etat de mobilité                                         #
# -Arrête la voiture quand demandé                                      #
# -Retourne false si la voiture s'arrête, true sinon                    #
#-----------------------------------------------------------------------#
def coupe(text, bouge):
    move = bouge
    if move :
        if "stop" in text or "arrêt" in text or "coque" in text :
            arretComplet()
            Vitesse1 = 30
            move = False
    return move 
    
    
arretComplet()
text_prec = ""
bouge = False
"""
while True:
    acceleration = 0
    data = stream.read(4096)
    if recognizer.AcceptWaveform(data):
        text = recognizer.Result()
        print(f"' {text[14:-3]} '")
    
        if "encor" in text:
            text = text_prec
            
        bouge               = avancer(text, bouge)      # Avancer ou reculer
        acceleration        = acc_ral(text, bouge)      # Accélérer ou ralentir ?
        Vitesse1, text_prec = accelerer(Vitesse1, acceleration)  
        text_prec           = text_prec + tourner(text) # Direction
        bouge               = coupe(Text, bouge)        #Arrêt
            
        #quitter le programme
        if "quitte" in text or "kit" in text :
            break
        text_prec = text 
"""
text = "avance acce fort droite stop"
bouge = avancer(text, bouge)
acceleration = acc_ral(text, bouge)      # Accélérer ou ralentir ?
accelerer(Vitesse1, acceleration) 
tourner(text)
sleep(2)
coupe(text, bouge)
