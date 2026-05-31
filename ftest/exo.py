#!/usr/bin/env python
print('bonjour','python')
nom=input('quel est ton nom?')
age=input('quel est ton age?')
age=int(age)+5
if age >= 18:
    print('ton nom est',nom,'et tu auras plus de 18 ans dans 5ans (plus precisement tu auras',age,'ans)')
else:
    print('ton nom est',nom,'et tu auras',age,'ans dans 5ans')
