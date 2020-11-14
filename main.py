#!/usr/bin/python3
# -*- coding: utf-8 -*-

import random
import copy
import pymysql
#import MySQLdb

from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, BaseFilter, MessageFilter
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import logging

#---local-import---

import DATABASE
import TOKEN

#---setup---

#setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logging.basicConfig(file="mybot.log.txt", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class DB:
	conn = None

	def connect(self):
		self.conn = pymysql.connect(host=DATABASE.host,  # your host
		user=DATABASE.user,       # username
		passwd=DATABASE.passwd,     # password
		db=DATABASE.db)       #database

	def squery(self, sql):
		try:
			cursor = self.conn.cursor()
			cursor.execute(sql)
		except (AttributeError, pymysql.OperationalError):
			self.connect()
			cursor = self.conn.cursor()
			cursor.execute(sql)
		return cursor

	def tquery(self, sql, tuple):
		try:
			cursor = self.conn.cursor()
			cursor.execute(sql, tuple)
		except (AttributeError, pymysql.OperationalError):
			self.connect()
			cursor = self.conn.cursor()
			cursor.execute(sql, tuple)
		return cursor

	def commit(self):
		self.conn.commit()

db = DB()

DEBUG = False

if DEBUG == True:
	sql = "SELECT * FROM user"
	cur = db.squery(sql)

	# print the first and second column
	for row in cur.fetchall() :
		print(row[0], " ", row[1])

#variables
gcreate = []
gtext= []
gjoin = []
feed = []
bug = []


#---main-funcions---

class FilterReply(MessageFilter):
	def filter(self, message):
		return bool(len(gcreate)+len(gjoin)+len(feed)+len(bug)+len(gtext))

def adminKey():
	keyboard = [[InlineKeyboardButton("Beitreten/Verlassen", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abbruch", callback_data='3')]]
	return InlineKeyboardMarkup(keyboard)

def adminKeyactive():
	keyboard = [[InlineKeyboardButton("Beitreten/Verlassen", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abbruch", callback_data='3')], [InlineKeyboardButton("erweiterte Nachricht deaktivieren", callback_data='5')]]
	return InlineKeyboardMarkup(keyboard)

def adminKeyinactive():
	keyboard = [[InlineKeyboardButton("Beitreten/Verlassen", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abbruch", callback_data='3')], [InlineKeyboardButton("erweiterte Nachricht aktivieren", callback_data='6')]]
	return InlineKeyboardMarkup(keyboard)

def userKey():
	keyboard = [[InlineKeyboardButton("Verlassen", callback_data='4')]]
	return InlineKeyboardMarkup(keyboard)

def createMessage(tmpUser, gameName, gameStatus):
	message="Spielname: "+str(gameName)+"\n"+"Status: "+str(gameStatus)+"\n"+"Spieler:"
	if len(tmpUser) != 0:
		for i in tmpUser:
			message += "\n- "+((str(i[2]) if str(i[0]) == "None" else (str(i[0])+" "+("" if str(i[1]) == "None" else str(i[1])))))
	return message

def updateMessage(context, gameName):
	print("updateMessage")
	cur = db.tquery("SELECT status, c_id, m_id, text FROM game WHERE name = %s", (gameName,))
	game = cur.fetchall()
	gameStatus = game[0][0]
	guID = game[0][1]
	gmID = game[0][2]
	hasUserText = game[0][3]
	cur = db.tquery("SELECT u.first_name, u.last_name, u.username, gu.c_id, gu.m_id FROM game_user gu INNER JOIN user u ON u.u_id = gu.c_id WHERE gu.g_name = %s", (gameName,))
	tmpUser = cur.fetchall()
	userID = []
	messageID = []
	message = createMessage(tmpUser, gameName, gameStatus)

	if gameStatus == "aktiv":
		if len(tmpUser) == 0:
			print(hasUserText)
			if hasUserText == 1:
				admin_markup = adminKeyactive()
			else:
				admin_markup = adminKeyinactive()
		else:
			admin_markup = adminKey()
		user_markup = userKey()
	else:
		admin_markup = None
		user_markup = None

	for i in tmpUser:
		userID.append(i[3])
		messageID.append(i[4])

	for i in range(len(userID)):
		if userID[i] != guID:
			context.bot.edit_message_text(text=message, chat_id=int(userID[i]), message_id=int(messageID[i]), reply_markup=user_markup)
	print(guID)
	print(gmID)
	context.bot.edit_message_text(text=message, chat_id=guID, message_id=gmID, reply_markup=admin_markup)

def checkUser(update, context):
	cur = db.squery("SELECT u_id, first_name, last_name, username FROM user")
	allUsers = cur.fetchall()
	theUser = []
	for user in allUsers:
		if user[0] == update.effective_user.id:
			theUser = user

	if len(theUser) == 0:
		cur = db.tquery("INSERT INTO user (u_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (update.effective_user.id, ("" if update.effective_user.first_name == None else update.effective_user.first_name), ("" if update.effective_user.last_name == None else update.effective_user.last_name), update.effective_user.username))
		db.commit()
	else:
		cur = db.tquery("UPDATE user SET first_name=%s, last_name=%s, username=%s WHERE u_id=%s", (update.effective_user.first_name, update.effective_user.last_name, update.effective_user.username, update.effective_user.id))
		db.commit()
	return True

def checkReply(update):
	if update.message.chat_id in gcreate:
		gcreate.remove(update.message.chat_id)
	if update.message.chat_id in gjoin:
		gjoin.remove(update.message.chat_id)
	if update.message.chat_id in feed:
		feed.remove(update.message.chat_id)
	if update.message.chat_id in bug:
		bug.remove(update.message.chat_id)
	if update.message.chat_id in gtext:
		gtext.remove(update.message.chat_id)

def rtd(context, gameUser, gameName):
	tmpUser = copy.deepcopy(gameUser)
	randa = []
	a = True
	while a:
		random.shuffle(tmpUser)
		random.shuffle(tmpUser)
		a = False
		for j in range(0, len(tmpUser)):
			if gameUser[j] == tmpUser[j]:
				a = True

	updateMessage(context, gameName)

	cur = db.tquery("SELECT text FROM game WHERE name = %s", (gameName,))
	userHasText = cur.fetchall()[0][0]
	print(userHasText)

	for i in range(0, len(gameUser)):
		context.bot.send_message(chat_id=gameUser[i][0], text="Hey "+str(gameUser[i][1])+", dein Wichtelpartner aus dem Spiel '"+gameName+"' ist "+str(tmpUser[i][1])+(("\n\n"+str(tmpUser[i][1])+" hat dir eine Nachricht hinterlassen:\n"+tmpUser[i][2]) if userHasText else "."))

def start(update, context):
	if update.message.chat.type == "private":
		checkUser(update, context)
		context.bot.send_message(chat_id=update.message.chat_id, text="Willkommen beim MCSecretSantaBot tippe /hilfe um mehr Informationen zu erhalten.")

def checkGame(update, context, name):
	cur = db.squery("SELECT name FROM game")
	game = cur.fetchall()
	gameName = []

	for i in game:
		gameName.append(i[0])

	if name in gameName:
		return True
	else:
		return False

def initgame(update, context, gameName):
	gameStatus = "aktiv"
	message = createMessage([], gameName, gameStatus)
	cur = db.tquery("INSERT INTO game (name, c_id, m_id, text, status) VALUES (%s, %s, %s, %s, %s)", (gameName, update.message.chat_id, update.message.message_id+1, False, gameStatus))
	db.commit()
	context.bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=adminKeyinactive())

def joingame(update, context, gameName):
	cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
	gameUser = cur.fetchall()
	userID = []

	for i in range(0, len(gameUser)):
		userID.append(gameUser[i][0])

	if update.message.from_user.id in userID:
		context.bot.send_message(chat_id=update.message.chat_id, text="Du bist dem Spiel berreits beigetreten.")
	else:
		cur = db.tquery("INSERT INTO game_user (g_name, c_id, m_id, user_text) VALUES (%s, %s, %s, %s)", (gameName, update.message.from_user.id, update.message.message_id+1, ""))
		db.commit()
		context.bot.send_message(chat_id=update.message.chat_id, text="Du bist '"+gameName+"' beigetreten!")
		updateMessage(context, gameName)
		cur = db.tquery("SELECT text FROM game WHERE name = %s", (gameName,))
		userHasText = cur.fetchall()[0][0]
		print(userHasText)
		if userHasText == 1:
			gtext.append([update.message.chat_id, update.message.message_id+1])
			context.bot.send_message(chat_id=update.message.chat_id, text="Das Spiel hat die erweiterte Nachricht aktiviert. Was möchtest du deinem Wichtelpartner mitteilen?")


def creategame(update, context):
	if checkUser(update, context):
		print("creategame")
		gameName = ""
		try:
			gameName = context.args[0]
		except:
			pass

		if not gameName == "":
			if not checkGame(update, context, gameName):
				initgame(update, context, gameName)
			else:
				context.bot.send_message(chat_id=update.message.chat_id, text="Ein Spiel mit diesem Namen läuft schon, bitte wähle einen anderen Namen.")
				checkReply(update)
				gcreate.append(update.message.chat_id)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, text="Wähle einen Namen für dein Spiel.")
			checkReply(update)
			gcreate.append(update.message.chat_id)

def join(update, context):
	if checkUser(update, context):
		print("join")
		gameName = ""
		try:
			gameName = str(context.args[0])
			print(gName)
		except:
			pass

		if not gameName == "":
			if checkGame(update, context, gameName):
				joingame(update, context, gameName)
			else:
				context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Ein Spiel mit diesem Namen gibt es nicht, bitte gib den Namen eines laufenden Spieles an.")
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Gib den Namen eines laufenden Spieles ein.")
			checkReply(update)
			gjoin.append(update.message.chat_id)

def buttonHandler(update, context):
	query = update.callback_query

	if checkUser(update, context):
		print("buttonHandler")
		reply_markup = adminKeyinactive()

		theUser = update.effective_user
		theMessage = query.message.text

		cur = db.tquery("SELECT name FROM game WHERE c_id = %s AND m_id = %s", (query.message.chat_id, query.message.message_id))
		game = cur.fetchall()
		if len(game) != 0:
			print(game)
			gameName = game[0][0]

		if query.data == '1': #Join/Exit
			cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
			gameUser = cur.fetchall()
			userID = []

			for i in range(0, len(gameUser)):
				userID.append(gameUser[i][0])

			if theUser.id in userID:
				cur = db.tquery("DELETE FROM game_user WHERE g_name = %s AND c_id = %s", (gameName, theUser.id))
				db.commit()
				updateMessage(context, gameName)
			else:
				cur = db.tquery("INSERT INTO game_user (g_name, c_id, m_id, user_text) VALUES (%s, %s, %s, %s)", (gameName, theUser.id, query.message.message_id, ""))
				db.commit()
				updateMessage(context, gameName)
				cur = db.tquery("SELECT text FROM game WHERE name = %s", (gameName,))
				userHasText = cur.fetchall()[0][0]
				print(userHasText)
				if userHasText == 1:
					gtext.append([query.message.chat_id, query.message.message_id])
					context.bot.send_message(chat_id=query.message.chat_id, text="Das Spiel hat die erweiterte Nachricht aktiviert. Was möchtest du deinem Wichtelpartner mitteilen?")

		elif query.data == '2':
			cur = db.tquery("SELECT c_id, user_text FROM game_user WHERE g_name = %s", (gameName,))
			tmpUser = cur.fetchall()
			tgameUser = []
			gameUser = []
			for i in range(len(tmpUser)):
				cur = db.tquery("SELECT first_name, last_name, username FROM user WHERE u_id = %s", (tmpUser[i][0],))
				tUser = cur.fetchall()
				tgameUser.append(int(tmpUser[i][0]))
				tgameUser.append(str(tUser[0][0])+str(tUser[0][1]))
				gameUser.append([int(tmpUser[i][0]), (str(tUser[0][2]) if str(tUser[0][0]) == "None" else (str(tUser[0][0]) +("" if str(tUser[0][1])== "None" else " "+str(tUser[0][1])))), str(tmpUser[i][1])])

			if len(gameUser) > 2:
				cur = db.tquery("UPDATE game SET status = %s WHERE name = %s", ("beendet", gameName))
				db.commit()
				rtd(context, gameUser, gameName)
				cur = db.tquery("DELETE FROM game_user WHERE g_name = %s", (gameName,))
				db.commit()
				cur = db.tquery("DELETE FROM game WHERE name = %s", (gameName,))
				db.commit()

		elif query.data == '3':
			cur = db.tquery("UPDATE game SET status = %s WHERE name = %s", ("abgebrochen", gameName))
			db.commit()
			updateMessage(context, gameName)
			cur = db.tquery("DELETE FROM game_user WHERE g_name = %s", (gameName,))
			db.commit()
			cur = db.tquery("DELETE FROM game WHERE name = %s", (gameName,))
			db.commit()

			context.bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id)


		elif query.data == '4':
			cur = db.tquery("SELECT name FROM game WHERE name = (SELECT g_name FROM game_user WHERE c_id = %s AND m_id = %s)", (query.message.chat_id, query.message.message_id))
			game = cur.fetchall()
			print(game)
			gameName = game[0][0]
			print("Exit")
			cur = db.tquery("DELETE FROM game_user WHERE g_name = %s AND c_id = %s", (gameName, theUser.id))
			db.commit()
			context.bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id, reply_markup=None)
			updateMessage(context, gameName)

		elif query.data == '5':
			cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
			gameUser = cur.fetchall()
			if(len(gameUser) == 0):
				cur = db.tquery("UPDATE game SET text = %s WHERE name = %s", (0, gameName))
				db.commit()
				updateMessage(context, gameName)
			else:
				context.bot.send_message(chat_id=update.message.chat_id, text="Es dürfen keine Spieler im Spiel sein um das zu ändern!")

		elif query.data == '6':
			cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
			gameUser = cur.fetchall()
			if(len(gameUser) == 0):
				cur = db.tquery("UPDATE game SET text = %s WHERE name = %s", (1, gameName))
				db.commit()
				updateMessage(context, gameName)
			else:
				context.bot.send_message(chat_id=update.message.chat_id, text="Es dürfen keine Spieler im Spiel sein um das zu ändern!")

def reply(update, context):
	checkMessage = False
	message_id = 0
	for user in gtext:
		print(user[0])
		if update.message.chat_id == user[0]:
			checkMessage = True
			message_id = user[1]

	if update.message.chat_id in gcreate:
		if checkGame(update, context, update.message.text):
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Ein Spiel mit diesem Namen läuft schon, bitte wähle einen anderen Namen.")
		else:
			initgame(update, context, update.message.text)
			gcreate.remove(update.message.chat_id)

	if update.message.chat_id in gjoin:
		if checkGame(update, context, update.message.text):
			joingame(update, context, update.message.text)
			gjoin.remove(update.message.chat_id)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Ein Spiel mit diesem Namen gibt es nicht, bitte gib den Namen eines laufenden Spieles an.")

	if update.message.chat_id in feed:
		cur = db.tquery("INSERT INTO feedback (f_id, text) VALUES (NULL, %s)", (update.message.text,))
		db.commit()
		context.bot.send_message(chat_id=update.message.chat_id, text="Danke für dein Feedback, das hilft um den Bot immer weiter zu verbessern.")
		feed.remove(update.message.chat_id)

	if update.message.chat_id in bug:
		cur = db.tquery("INSERT INTO bugreport (b_id, text) VALUES (NULL, %s)", (update.message.text,))
		db.commit()
		context.bot.send_message(chat_id=update.message.chat_id, text="Danke für den Fehlerberricht, das Problem wird so schnell wie Möglich angegangen.")
		bug.remove(update.message.chat_id)

	if checkMessage:
		print(gtext)
		cur = db.tquery("UPDATE game_user SET user_text = %s WHERE c_id = %s AND m_id = %s", (update.message.text, update.message.chat_id, message_id))
		db.commit()
		gtext.remove([update.message.chat_id, message_id])

def gamerules(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Anleitung:\nZunächst muss ein neues Spiel gestartet werden, nutze dafür den Befehl /neu.\nDanach können andere Spieler dem Spiel mit dem Befehl /spiel beitreten\nWenn alle dem Spiel beigetreten sind kann der Administrator das Spiel Starten.\nNachdem das Spiel dann gestartet wurde bekommt jeder seinen Wichtelpartner zugewiesen.")

def help(update, context):
	update.message.reply_text("Kommandoliste:\n/start - um den Chat mit MCSecretSantaBot zu starten.\n/anleitung - um eine Spielanleitung zu bekommen.\n/neu [Spielname]- um ein Spiel zu erstellen.\n/spiel - um einem Spiel beizutreten\n/hilfe - um alle Kommandos angezeigt zu bekommen.\n/feedback - um deine Meinung über den Bot mitzuteilen.\n/fehlermeldung - wenn ein Fehler augetreten ist.")

def feedback(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Bitte gib deine Rückmeldung an.")
	checkReply(update)
	feed.append(update.message.chat_id)

def bugreport(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Bitte gib an was schiefgelaufen ist.")
	checkReply(update)
	bug.append(update.message.chat_id)

def error(update, context):
	#Log Errors caused by Updates.
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def unknown(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Tut mir leid, den Befehl kenne ich nicht.")

def secretsanta():
	#---setup---

	filter_reply = FilterReply()

	#set telegram updater
	updater = Updater(token=TOKEN.token, use_context=True)

	#easy name for dispatcher
	dp = updater.dispatcher

	dp.add_error_handler(error)
	dp.add_handler(CommandHandler('hilfe', help))
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('neu', creategame, pass_args=True))
	dp.add_handler(CommandHandler('spiel', join, pass_args=True))
	dp.add_handler(CallbackQueryHandler(buttonHandler))
	dp.add_handler(CommandHandler('anleitung', gamerules))
	dp.add_handler(CommandHandler('feedback', feedback))
	dp.add_handler(CommandHandler('fehlermeldung', bugreport))
	dp.add_handler(MessageHandler(Filters.command, unknown))
	dp.add_handler(MessageHandler(filter_reply, reply))

	#---start-bot---
	updater.start_polling()
	print("\n---Bot Gestartet---")
	updater.idle()

def main():
	secretsanta()

if __name__ == '__main__':
	main()
