#!/usr/bin/pyton
# -*- coding: utf-8 -*-

import random
import copy
import MySQLdb

from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, BaseFilter
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import logging

#---local-import---

import DATABASE
import TOKEN

#---setup---

#setup logging
logging.basicConfig(file="mybot.log.txt", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class DB:
	conn = None

	def connect(self):
		self.conn = MySQLdb.connect(host=DATABASE.host,  # your host
		user=DATABASE.user,       # username
		passwd=DATABASE.passwd,     # password
		db=DATABASE.db)       #database

	def squery(self, sql):
		try:
			cursor = self.conn.cursor()
			cursor.execute(sql)
		except (AttributeError, MySQLdb.OperationalError):
			self.connect()
			cursor = self.conn.cursor()
			cursor.execute(sql)
		return cursor

	def tquery(self, sql, tuple):
		try:
			cursor = self.conn.cursor()
			cursor.execute(sql, tuple)
		except (AttributeError, MySQLdb.OperationalError):
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
		print row[0], " ", row[1]

#variables
gcreate = []
gjoin = []
feed = []
bug = []


#---main-funcions---

class FilterReply(BaseFilter):
	def filter(self, message):
		return bool(len(gcreate)+len(feed)+len(bug))

def adminKey():
	keyboard = [[InlineKeyboardButton("Join/Exit", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abort", callback_data='3')]]
	return InlineKeyboardMarkup(keyboard)

def userKey():
	keyboard = [InlineKeyboardButton("Exit", callback_data='4')]
	return InlineKeyboardMarkup(keyboard)

def updateMessage(context, gameID):
	cur = db.tquery("SELECT message, u_id, m_id FROM game WHERE g_id = %s", (gameID,))
	game = cur.fetchall()
	message = game[0][0]
	guID = game[0][1]
	gmID = game[0][2]
	cur = db.tquery("SELECT u.first_name, u.last_name, u.u_id, gu.m_id FROM user AS u, game_user AS gu WHERE gu.u_id = u.u_id AND gu.g_id = %s", (gameID,))
	tmpUser = cur.fetchall()
	userID = []
	messageID = []
	for i in tmpUser:
		print i
		message += ("\n- "+str(i[0])+" "+str(i[1]))
		userID.append(i[2])
		messageID.append(i[3])
	
	for i in range(len(userID)):
		print userID[i]
		print gameID
		if userID[i] != guID:
			print "true"
			reply_markup = userKey()
			context.bot.edit_message_text(text=message, chat_id=int(userID[i]), message_id=int(messageID[i]), reply_markup=reply_markup)

	print guID
	print gmID
	reply_markup = adminKey()
	context.bot.edit_message_text(text=message, chat_id=guID, message_id=gmID, reply_markup=reply_markup)

def checkUser(update, context, message):
	cur = db.squery("SELECT u_id FROM user")
	allUsers = cur.fetchall()
	theUsers = []
	for row in allUsers:
		theUsers.append(int(row[0]))

	if message.from_user.id not in theUsers:
		cur = db.tquery("INSERT INTO user (u_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username))
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

def rtd(context, gameUser, theGame):
	tmpUser = copy.deepcopy(gameUser)
	randa = []
	a = True
	while a:
		random.shuffle(tmpUser)
		a = False
		for j in range(0, len(tmpUser)):
			if gameUser[j] == tmpUser[j]:
				a = True


	for i in range(0, len(gameUser)):
		context.bot.send_message(chat_id=gameUser[i], text="Hey "+ gameUser[i]+", the Player I chose for you in the game '"+theGame+"' is "+tmpUser[i])

def start(update, context):
	if update.message.chat.type == "private":
		checkUser(update, context, update.message)
		context.bot.send_message(chat_id=update.message.chat_id, text="Welcome to MCSecretSantaBot type /help for more information")
	else:
		context.bot.send_message(chat_id=update.message.chat_id, text="I'm sorry, this only works in private chat with me!")

def checkGame(update, context, name):
	cur = db.squery("SELECT name FROM game")
	game = cur.fetchall()
	gameName = []

	for i in game:
		gameName.append(game[i][0])

	if name in gameName:
		return True
	else:
		return False

def initgame(update, context, gName):
	message = "game: "+str(gName)+"\nstatus: waiting for players!\nadmin: "+("" if update.message.from_user.first_name == None else str(update.message.from_user.first_name))+" "+("" if update.message.from_user.last_name == None else str(update.message.from_user.last_name)+"\n\nmembers:\n")
	cur = db.tquery("INSERT INTO game (g_id, u_id, m_id, name, message) VALUES (NULL, %s, %s, %s, %s)", (update.message.chat_id, update.message.message_id+1, gName, message))
	db.commit()
	context.bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=adminKey())

def joingame(update, context, gName):
	cur = db.tquery("SELECT u_id FROM user WHERE u_id = (SELECT u_id FROM game_user WHERE g_id = (SELECT g_id FROM game WHERE name = %s)))", (gName,))
	gameUser = cur.fetchall()
	userID = []

	for i in range(0, len(gameUser)):
		userID.append(gameUser[i][0])

	if update.message.from_user.id in userID:
		context.bot.send_message(chat_id=update.message.chat_id, text="You are already in the game!")
	else:
		cur = db.tquery("SELECT g_id FROM game WHERE name = %s)", (gName,))
		gameID = cur.fetchall()[0]

		cur = db.tquery("INSERT INTO game_user (gu_id, g_id, u_id, m_id) VALUES (NULL, %s, %s, %s)", (gameID, update.message.from_user.id, update.message.message_id+1))
		db.commit()
		updateMessage(context, gameID)

def creategame(update, context):
	if checkUser(update, context, update.message):
		gName = ""
		try:
			gName = context.args[0]
		except:
			pass

		if not gName == "":
			if not checkGame(update, context, gName):
				initgame(update, context, gName)
			else:
				context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name is already running!\nPlease type in a different name.")
				checkReply(update)
				gcreate.append(update.message.chat_id)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name")
			checkReply(update)
			gcreate.append(update.message.chat_id)

def join(update, context):
	if checkUser(update, context, update.message):
		gName = ""
		try:
			gName = context.args[0]
		except:
			pass
		if not gName == "":
			joingame(update, context, gName)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name")
			checkReply(update)
			gjoin.append(update.message.chat_id)

def buttonHandler(update, context):
	query = update.callback_query

	if checkUser(query, context, query):
		reply_markup = adminKey()

		theUser = query.from_user
		theMessage = query.message.text

		cur = db.tquery("SELECT g_id, m_id, name, message FROM game WHERE u_id = %s AND m_id = %s", (query.message.chat_id, query.message.message_id))
		game = cur.fetchall()
		gameId = game[0][0]
		gmID = game[0][1]
		theGame = game[0][2]
		message = game[0][3]

		if query.data == '1':
			cur = db.tquery("SELECT u_id FROM user WHERE u_id = (SELECT u_id FROM game_user WHERE g_id = %s)", (gameId,))
			gameUser = cur.fetchall()
			userID = []

			for i in range(0, len(gameUser)):
				userID.append(gameUser[i][0])

			if theUser.id in userID:
				cur = db.tquery("DELETE FROM game_user WHERE g_id = %s AND u_id = %s", (gameId, theUser.id))
				db.commit()
				updateMessage(context, gameId)
			else:
				cur = db.tquery("INSERT INTO game_user (gu_id, g_id, u_id, m_id) VALUES (NULL, %s, %s, %s)", (gameId, theUser.id, query.message.message_id))
				db.commit()
				updateMessage(context, gameId)

		elif query.data == '2':
			cur = db.tquery("SELECT u_id FROM game_user WHERE g_id = %s", (gameId,))
			tmpUser = cur.fetchall()
			gameUser = []
			for i in range(len(tmpUser)):
				gameUser.append(tmpUser[i][0])

			if len(gameUser) > 2:
				rtd(context, gameUser, theGame)
				for i in range(0, len(theMessage)):
					if theMessage[i:i+6] == "status":
						for j in range(i, len(theMessage)):
							if theMessage[j] == '!':
								bg = theMessage[0:i+8]
								en = theMessage[j+1:len(theMessage)]
								theMessage = bg + "started!" + en
								break
						break

				cur = db.tquery("DELETE FROM game_user WHERE g_id = %s", (gameId,))
				db.commit()
				cur = db.tquery("DELETE FROM game WHERE g_id = %s", (gameId,))
				db.commit()

				context.bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id)
			else:
				context.bot.send_message(chat_id=query.message.chat_id, text="I'm Sorry, this game does only make sense with 3 or more Players")

		elif query.data == '3':
			for i in range(0, len(theMessage)):
				if theMessage[i:i+6] == "status":
					for j in range(i, len(theMessage)):
						if theMessage[j] == '!':
							bg = theMessage[0:i+8]
							en = theMessage[j+1:len(theMessage)]
							theMessage = bg + "aborted!" + en
							break
					break
			cur = db.tquery("DELETE FROM game_user WHERE g_id = %s", (gameId,))
			db.commit()
			cur = db.tquery("DELETE FROM game WHERE g_id = %s", (gameId,))
			db.commit()

			context.bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id)

def reply(update, context):
	if update.message.chat_id in gcreate:
		if checkGame(update, context, update.message.text):
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="A game with this name is already running!\nPlease type in a different name.")
		else:
			initgame(update, context, update.message.text)
			gcreate.remove(update.message.chat_id)

	if update.message.chat_id in gjoin:
		cur = db.squery("SELECT name FROM game")
		gName = cur.fetchall()
		if update.message.text in gName:
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
	print "\nstarted"
	updater.idle()

def main():
	secretsanta()

if __name__ == '__main__':
	main()
