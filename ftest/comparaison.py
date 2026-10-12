#!/usr/bin/env python
print("saisissez trois valeur")
x=int(input('x=:'))
y=int(input('y=:'))
z=int(input('z=:'))
if x>y and x>z:
    print("le plus grand des trois est :",x)
elif y>x and y>z:
    pring("le plus grand des trois est :",y)
elif z>x and z>y:
    print("le plus grand des trois est :",z)
else:
    print("impossible de determiner le plus grand!")

