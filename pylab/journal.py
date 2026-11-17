#!/usr/bin/env python
#importation des modules 
import os
import pathlib
import math
#initialisation du dictionnaire contenant les données

data={}
data['date']=input('date du trade: ')
data['optime']=input("heure d'ouverture: ")
data['cltime']=input("heure de cloture: ")
data['session']=input("session du trade: ")
data['inst']=input("paire tradé: ")
data['lot']=input("lot: ")
data['tf']=input('time frame: ')
data['type']=input('buy or sell: ')
data['rr']=input('ratio: ')
data['ar']=input('argent risqué: '+'$')
data['pe']=input("prix d'entré: ")
data['ps']=input("prix de sorti: ")
data['sl']=input('sl: ')
data['tp']=input('tp: ')
data['pnl']=input('pnl: '+'$')
data['capA']=input('capital avant: '+'$')
data['capAp']=input('capital aprés: '+'$')
data['plan']=input('avez vous respecte le plan? oui/non: ')
data['setup']=input('setup du trade: ')
data['conflu']=input('confluance: ')
data['note']=input('note sur le trade: ')

#definition de quelques fonctionnalites

ask=input('voulez vous connaitre vos données actuelles?? oui/non')
if ask=='oui':




else: 
