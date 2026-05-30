# --- Ton premier script sur Pydroid ---

films = {
    "action": "John Wick",
    "romance": "Titanic",
    "nature": "Le documentaire sur les lamas"
}

# Demande à l'utilisateur (une petite fenêtre surgira sur Pydroid)
choix = input("Quel genre aimes-tu ? (action, romance, nature) : ").lower()

# Vérification
if choix in films:
    print(f"\n✨ IA : Alors je te conseille : {films[choix]} !")
else:
    print("\n❌ IA : Désolé, je ne connais pas encore ce genre.")
