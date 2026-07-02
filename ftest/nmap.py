#!/usr/bin/env python
#(#_#) ;) je kiffe l'informatique 
import os
user=input('entrer votre nom:')
print('salut :)',user,'ceci est un programme de scan nmap avec trois type de scan possible sV(1),A(2) et sn(3)' )
op=int(input('choisissez une option pour le scan (1,2,3):'))
if op==1:
    scan=input("mettez l'adresse à scanner:")
    print('scan en cours... le resultat sera enregistrez dans rapport.txt')
    resulta=os.system(f"nmap -sV {scan} > rapport.txt")
elif op==2:
    scan=input("mettez l'adresse à scanner:")
    print('scan en cours... le resultat sera enregitrez dans rapport.txt')
    resulta=os.system(f"nmap -A {scan} > rapport.txt")
elif op==3:
    scan=input("mettez l'adresse à scanner:")
    print('scan en cours... le resultat sera enregistrez dans rapport.txt')
    resulta=os.system(f"nmap -sn {scan} > rapport.txt")
print('les resultats du scan sont maintenant dispo dans rapport.txt ;)')
