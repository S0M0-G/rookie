#!/usr/bin/env python
#projet:assistant d'aide pour atteindre ces objectifs'
#+un p'tit essai pour voir ma maitrise des liste
#d'abord un p'tit salut'
print ('hello master what are us doing today?')
#def de la liste contenant les options à choisir 
goal = ['coding','studing','learning','building app','gaming']
#demande à l'utilisateur de faire un choix parmis ceux present'
answer = input ('choise one option between (coding,studing,learning,building app,gaming):')
#mise en place de la reponse selon le choix de l'utilisateur'
if answer in goal:
	print ('ok master we will going to do',answer)
	if answer == 'coding':
		print ('now we going to practice python')
	if answer == 'studing':
		print ("let's go for some maths exercise")
	if answer == 'learning':
		print ('good option is time for news knowledge')
	if answer == 'building app':
		print ('which type of app we will build?')
	if answer == 'gaming':
		print (":) time to do a small break master") 
	print ('a day goal is succed good bye master for the next session')
#reponse si le choix de l'utilisateur ne correspond pas à ceux proposés'
else:
	print ("[-_-] ehh master this choise isn't in our planning so please choise another option you must become a GOAT ;)")

