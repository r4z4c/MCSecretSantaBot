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
gjoin = []
feed = []
bug = []


#---main-funcions---

class FilterReply(MessageFilter):
	def filter(self, message):
		return bool(len(gcreate)+len(gjoin)+len(feed)+len(bug))

def adminKey():
	keyboard = [[InlineKeyboardButton("Beitreten/Verlassen", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abbruch", callback_data='3')]]
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
	cur = db.tquery("SELECT status, c_id, m_id FROM game WHERE name = %s", (gameName,))
	game = cur.fetchall()
	gameStatus = game[0][0]
	guID = game[0][1]
	gmID = game[0][2]
	cur = db.tquery("SELECT u.first_name, u.last_name, u.username, gu.c_id, gu.m_id FROM game_user gu INNER JOIN user u ON u.u_id = gu.c_id WHERE gu.g_name = %s", (gameName,))
	tmpUser = cur.fetchall()
	print(tmpUser)
	userID = []
	messageID = []
	message = createMessage(tmpUser, gameName, gameStatus)

	if gameStatus == "aktiv":
		admin_markup = adminKey()
		user_markup = userKey()
	else:
		admin_markup = None
		user_markup = None

	for i in tmpUser:
		userID.append(i[3])
		messageID.append(4)

	for i in range(len(userID)):
		if userID[i] != guID:
			print(userID[i])
			print(messageID[i])
			context.bot.edit_message_text(text=message, chat_id=int(userID[i]), message_id=int(messageID[i]), reply_markup=user_markup)
	print(guID)
	print(gmID)
	context.bot.edit_message_text(text=message, chat_id=guID, message_id=gmID, reply_markup=admin_markup)

def checkUser(update, context):
	cur = db.squery("SELECT u_id FROM user")
	allUsers = cur.fetchall()
	theUsers = []
	for row in allUsers:
		theUsers.append(int(row[0]))

	if update.message.from_user.id not in theUsers:
		cur = db.tquery("INSERT INTO user (u_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (update.message.from_user.id, ("" if update.message.from_user.first_name == None else update.message.from_user.first_name), ("" if update.message.from_user.last_name == None else update.message.from_user.last_name), update.message.from_user.username))
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

	for i in range(0, len(gameUser)):
		context.bot.send_message(chat_id=gameUser[i][0], text="Hey "+str(gameUser[i][1])+", dein Wichtelpartner aus dem Spiel '"+gameName+"' ist "+str(tmpUser[i][1]))

def start(update, context):
	if update.message.chat.type == "private":
		checkUser(update, context)
		context.bot.send_message(chat_id=update.message.chat_id, text="Willkommen im MCSecretSantaBot tippe /help um mehr Informationen zu erhalten.")

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
	context.bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=adminKey())

def joingame(update, context, gameName):
	cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
	gameUser = cur.fetchall()
	userID = []

	for i in range(0, len(gameUser)):
		userID.append(gameUser[i][0])

	if update.message.from_user.id in userID:
		context.bot.send_message(chat_id=update.message.chat_id, text="Du bist dem Spiel berreits beigetreten.")
	else:
		print(context.bot.send_message(chat_id=update.message.chat_id, text="Du bist drin!"))
		cur = db.tquery("INSERT INTO game_user (g_name, c_id, m_id, user_text) VALUES (%s, %s, %s, %s)", (gameName, update.message.from_user.id, update.message.message_id+1, ""))
		db.commit()
		updateMessage(context, gameName)

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
				context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name is already running!\nPlease type in a different name.")
				checkReply(update)
				gcreate.append(update.message.chat_id)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name")
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
				context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name does not exist!\nPlease type in a existing gamename.")
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name")
			checkReply(update)
			gjoin.append(update.message.chat_id)

def buttonHandler(update, context):
	query = update.callback_query

	if checkUser(query, context):
		print("buttonHandler")
		reply_markup = adminKey()

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
				print(theUser)
				cur = db.tquery("INSERT INTO game_user (g_name, c_id, m_id, user_text) VALUES (%s, %s, %s, %s)", (gameName, theUser.id, query.message.message_id, ""))
				db.commit()
				updateMessage(context, gameName)

		elif query.data == '2':
			cur = db.tquery("SELECT c_id FROM game_user WHERE g_name = %s", (gameName,))
			tmpUser = cur.fetchall()
			tgameUser = []
			gameUser = []
			for i in range(len(tmpUser)):
				cur = db.tquery("SELECT first_name, last_name, username FROM user WHERE u_id = %s", (tmpUser[i][0],))
				tUser = cur.fetchall()
				tgameUser.append(int(tmpUser[i][0]))
				tgameUser.append(str(tUser[0][0])+str(tUser[0][1]))
				gameUser.append([int(tmpUser[i][0]), (str(tUser[0][2]) if str(tUser[0][0]) == "None" else (str(tUser[0][0]) +("" if str(tUser[0][1])== "None" else " "+str(tUser[0][1]))))])

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

def reply(update, context):
	if update.message.chat_id in gcreate:
		if checkGame(update, context, update.message.text):
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name is already running!\nPlease type in a different name.")
		else:
			initgame(update, context, update.message.text)
			gcreate.remove(update.message.chat_id)

	if update.message.chat_id in gjoin:
		if checkGame(update, context, update.message.text):
			joingame(update, context, update.message.text)
			gjoin.remove(update.message.chat_id)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name does not exist!\nPlease type in a existing gamename.")

	if update.message.chat_id in feed:
		context.bot.send_message(chat_id=update.message.chat_id, text="Thank you for your feedback, I appreciate your time and thank you for using the bot.")
		feed.remove(update.message.chat_id)

	if update.message.chat_id in bug:
		context.bot.send_message(chat_id=update.message.chat_id, text="Thank you for reporting the bug, I will try to fix this as soon as possible.")
		bug.remove(update.message.chat_id)

def gamerules(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Rules:\nFirstly add me to a group.\nSecondly type in '/creategame [gamename]'.\nThirdly all users that want to play with you have to start a privat chat with me, then click the 'Join' button.\nAt the End the user who created the game (the admin) has to click 'Start'.\n\nOnce the game is started, each user gets a privat message from me with the randomly chosen player, the user has to get a gift for.")

def help(update, context):
	update.message.reply_text("Commandlist:\n/start - for starting a conversation with MCSecretSantaBot\n/gamerules - for displaying the rules of the game\n/creategame [game name] - for creating a new game\n/help - for this help message\n/feedback - for improving the bot experience\n/bugreport - for reporting bugs")

def feedback(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Please type in the Feedback")
	checkReply(update)
	feed.append(update.message.chat_id)

def bugreport(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Please type in the Bugreport")
	checkReply(update)
	bug.append(update.message.chat_id)

def error(update, context):
	#Log Errors caused by Updates.
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def unknown(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

def secretsanta():
	#---setup---

	filter_reply = FilterReply()

	#set telegram updater
	updater = Updater(token=TOKEN.token, use_context=True)

	#easy name for dispatcher
	dp = updater.dispatcher

	dp.add_error_handler(error)
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('creategame', creategame, pass_args=True))
	dp.add_handler(CommandHandler('join', join, pass_args=True))
	dp.add_handler(CallbackQueryHandler(buttonHandler))
	dp.add_handler(CommandHandler('gamerules', gamerules))
	dp.add_handler(CommandHandler('feedback', feedback))
	dp.add_handler(CommandHandler('bugreport', bugreport))
	dp.add_handler(MessageHandler(Filters.command, unknown))
	dp.add_handler(MessageHandler(filter_reply, reply))

	#---start-bot---
	updater.start_polling()
	print("\nstarted")
	updater.idle()

def main():
	secretsanta()

if __name__ == '__main__':
	main()
