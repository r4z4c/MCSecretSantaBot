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

sql = "SELECT * FROM user"
cur = db.squery(sql)

# print the first and second column
for row in cur.fetchall() :
	print row[0], " ", row[1]

#variables
gcreate = []
feed = []
bug = []


#---main-funcions---

class FilterReply(BaseFilter):
	def filter(self, message):
		return bool(len(gcreate)+len(feed)+len(bug))

def checkUser(update, context, message):
	cur = db.squery("SELECT u_id FROM user")
	allUsers = cur.fetchall()
	theUsers = []
	for row in allUsers:
		theUsers.append(int(row[0]))

	if message.from_user.id not in theUsers:
		cur = db.tquery("INSERT INTO user (u_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username))
		db.commit()

	cur = db.squery("SELECT c_id FROM chat")
	allChats = cur.fetchall()
	theChats = []
	for row in allChats:
		theChats.append(long(row[0]))

	if long(update.message.chat_id) not in theChats:
		cur = db.tquery("INSERT INTO chat (c_id, u_id, type) VALUES (%s, %s, %s)", (update.message.chat_id, message.from_user.id, update.message.chat.type))
		db.commit()

	return True

def rtd(context, theChat, theGame):
	theUser = []
	for i in range(len(theChat)):
		cur = db.tquery("SELECT first_name, last_name FROM user WHERE u_id = (SELECT u_id FROM chat WHERE c_id = %s)", (theChat[i],))
		theUser.append(cur.fetchall()[0][0])

	tmpUser = copy.deepcopy(theUser)
	randa = []
	a = True
	while a:
		random.shuffle(tmpUser)
		a = False
		for j in range(0, len(tmpUser)):
			if theUser[j] == tmpUser[j]:
				a = True


	for t in range(0, len(theUser)):
		context.bot.send_message(chat_id=theChat[t], text="Hey "+ theUser[t]+", the Player I chose for you, in the game '"+theGame+"' , is "+tmpUser[t])

def adminKey():
	keyboard = [[InlineKeyboardButton("Join/Exit", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abort", callback_data='3')]]
	return InlineKeyboardMarkup(keyboard)


def start(update, context):
	if update.message.chat.type == "private":
		if not checkUser(update, context, update.message):
			context.bot.send_message(chat_id=update.message.chat_id, text="Welcome to MCSecretSantaBot type /help for more info's")
	else:
		context.bot.send_message(chat_id=update.message.chat_id, text="I'm sorry, this only works in private chat with me!")


def creategame(update, context):
	if checkUser(update, context, update.message):
		gName = ""
		try:
			gName = context.args[0]
		except:
			pass

		if not gName == "":
			initgame(update, context, gName)
		else:
			context.bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name")
			gcreate.append(update.message.chat_id)

def buttonHandler(update, context):
	query = update.callback_query

	if checkUser(query, context, query):
		reply_markup = adminKey()

		theUser = query.from_user
		theMessage = query.message.text

		sql = "SELECT g_id, name FROM game WHERE c_id = %s AND m_id = %s"
		tuple = (query.message.chat_id, query.message.message_id)
		cur = db.tquery(sql, tuple)
		sql = cur.fetchall()
		gameId = sql[0][0]
		theGame = sql[0][1]

		if query.data == '1':
			isMember = True
			for i in range(0, len(theMessage)):
				if theMessage[i:i+len(theUser.first_name)+2] == "- "+theUser.first_name:
					theMessage = theMessage[0:i-1]+theMessage[i+len(theUser.first_name)+3:len(theMessage)]
					sql = "DELETE FROM game_user WHERE g_id = %s AND u_id = %s"
					tuple = (gameId, theUser.id)
					cur = db.tquery(sql, tuple)
					db.commit()
					context.bot.edit_message_text(text=theMessage, chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=reply_markup)
					isMember = False
					break

			if isMember:
				sql = "INSERT INTO game_user (gu_id, g_id, u_id) VALUES (NULL, %s, %s)"
				tuple = (gameId, theUser.id)
				cur = db.tquery(sql, tuple)
				db.commit()
				context.bot.edit_message_text(text=theMessage+"\n - "+theUser.first_name, chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=reply_markup)

		elif query.data == '2':
			cur = db.tquery("SELECT u_id FROM game_user WHERE g_id = (SELECT g_id FROM game WHERE g_id = %s)", (gameId,))
			GameUser = cur.fetchall()
			theChat = []
			for i in range(len(GameUser)):
				cur = db.tquery("SELECT c_id FROM chat WHERE u_id = (SELECT u_id FROM user WHERE u_id = %s)", (GameUser[i][0],))
				theChat.append(cur.fetchall()[0][0])

			if len(theChat) > 2:
				rtd(context, theChat, theGame)
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

def initgame(update, context, gName):
	cur = db.tquery("INSERT INTO game (g_id, c_id, m_id, name) VALUES (NULL, %s, %s, %s)", (update.message.chat_id, update.message.message_id+1, gName))
	db.commit()
	context.bot.send_message(chat_id=update.message.chat_id, text="game: "+gName+"\nstatus: waiting for players!\nadmin: "+("" if update.message.from_user.first_name == None else update.message.from_user.first_name)+" "+("" if update.message.from_user.last_name == None else update.message.from_user.last_name)+"\n\nmembers:\n", reply_markup=adminKey())

def reply(update, context):
	if update.message.chat_id in gcreate:
		initgame(update, context, update.message.text)
		gcreate.remove(update.message.chat_id)

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
	feed.append(update.message.chat_id)

def bugreport(update, context):
	context.bot.send_message(chat_id=update.message.chat_id, text="Please type in the Bugreport")
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
	dp.add_handler(CallbackQueryHandler(buttonHandler))
	dp.add_handler(CommandHandler('gamerules', gamerules))
	dp.add_handler(CommandHandler('feedback', feedback))
	dp.add_handler(CommandHandler('bugreport', bugreport))
	dp.add_handler(MessageHandler(Filters.command, unknown))
	dp.add_handler(MessageHandler(filter_reply, reply))

	#---start-bot---
	updater.start_polling()
	updater.idle()

def main():
	secretsanta()

if __name__ == '__main__':
	main()
