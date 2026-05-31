#!/usr/bin/env python
films = {
    "action": "John Wick",
    "romance": "Titanic",
    "nature": "Le documentaire sur les lamas"
}

choix = input("Quel genre aimes-tu ? (action, romance, nature) : ").lower()

if choix in films:
    print(f"\n✨ IA : Alors je te conseille : {films[choix]} !")
else:
    print("\n❌ IA : Désolé, je ne connais pas encore ce genre.")
