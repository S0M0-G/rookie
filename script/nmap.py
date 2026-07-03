#!/usr/bin/env python
#(#_#) ;) je kiffe l'informatique 
import os
user=input('entrer votre nom:')
print('salut :)',user,'ceci est un programme de scan nmap avec 9 types de scan possible: sV(1),A(2),sn(3),Pn(4),F(5),O(6),sS(7),script vuln(8),script auth(9)' )
scan=input("mettez l'adresse à scanner:")
op=int(input('choisissez une option pour le scan (1,2,3,4,5,6,7,8,9):'))
print('scan en cours... le resultat sera enregistrez dans rapport.txt')
if op==1:
    resulta=os.system(f"nmap -sV {scan} > rapport.txt")
elif op==2:
    resulta=os.system(f"nmap -A {scan} > rapport.txt")
elif op==3:
    resulta=os.system(f"nmap -sn {scan} > rapport.txt")
elif op==4:
    resulta=os.system(f"nmap -Pn {scan} > rapport.txt")
elif op==5:
    resulta=os.system(f"nmap -F {scan} > rapport.txt")
elif op==6:
    resulta=os.system("nmap -O {scan} > rapport.txt")
elif op==7:
    resulta=os.system(f"nmap -sS {scan} > rapport.txt")
elif op==8:
    resulta=os.system(f"nmap --script vuln {scan} > rapport.txt")
elif op==9:
    resulta=os.system(f"nmap --script auth {scan} > rapport.txt")
print('les resultats du scan sont maintenant dispo dans rapport.txt ;)')
