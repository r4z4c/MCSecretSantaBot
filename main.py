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

def checkData(bot, update, message, save=True):
	cur = db.squery("SELECT u_id FROM user")
        allUsers = cur.fetchall()
        theUsers = []
        isSaved = True
        for row in allUsers:
                theUsers.append(int(row[0]))

        if message.from_user.id not in theUsers:
                if save:
                        cur = db.tquery("INSERT INTO user (u_id, first_name, last_name, username) VALUES (%s, %s, %s, %s)", (message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username))
                        db.commit()
                if not update.message.chat.type == "private":
                       bot.send_message(chat_id=update.message.chat_id, text="Please go to @MCSecretSantaBot first and type in /start")
                isSaved = False

        cur = db.squery("SELECT c_id FROM chat")
        allChats = cur.fetchall()
        theChats = []
        for row in allChats:
                theChats.append(long(row[0]))

        if long(update.message.chat_id) not in theChats:
                if update.message.chat.type == "private":
			if save:
	                        cur = db.tquery("INSERT INTO chat (c_id, u_id, type) VALUES (%s, %s, %s)", (update.message.chat_id, message.from_user.id, update.message.chat.type))
        	                db.commit()
			isSaved = False
                else:
                        cur = db.tquery("INSERT INTO chat (c_id, u_id, type) VALUES (%s, %s, %s)", (update.message.chat_id, 0, update.message.chat.type))
                        db.commit()

	return isSaved

def rtd(bot, theChat, theGame):
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
		bot.send_message(chat_id=theChat[t], text="Hey "+ theUser[t]+", the Player I chose for you, in the game '"+theGame+"' , is "+tmpUser[t])

def inlineKey():
	keyboard = [[InlineKeyboardButton("Join/Exit", callback_data='1')],[InlineKeyboardButton("Start", callback_data='2'), InlineKeyboardButton("Abort", callback_data='3')]]
        return InlineKeyboardMarkup(keyboard)


def start(update, context):
	if update.message.chat.type == "private":
		if not checkData(context.bot, update, update.message):
			context.bot.send_message(chat_id=update.message.chat_id, text="Welcome to MCSecretSanta type /help for more info")
		else:
			context.bot.send_message(chat_id=update.message.chat_id, text="Welcome back "+update.message.from_user.first_name+" "+update.message.from_user.last_name)
	else:
		context.bot.send_message(chat_id=update.message.chat_id, text="I'm sorry, this only works in privat chat with me!")


def creategame(bot, update, args):
	if checkData(bot, update, update.message, save=False):
		gName = ""
		try:
			gName = args[0]
		except:
			pass

		if update.message.chat.type == "private" or update.message.chat.type == "channel":
			bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Please add the Bot to a group and then type /creategame again")
		else:
			if not gName == "":
				initgame(bot, update, gName)
			else:
				reply_markup = ForceReply(selective=True)
				bot.send_message(chat_id=update.message.chat_id, reply_to_message_id=update.message.message_id, text="Type in the game name", reply_markup=reply_markup)
       				gcreate.append(update.message.chat_id)

def buttonHandler(bot, update):
	query = update.callback_query

	if checkData(bot, query, query, save=False):
	        reply_markup = inlineKey()

		theUser = query.from_user
		theMessage = query.message.text

		sql = "SELECT g_id, admin, name FROM game WHERE c_id = %s AND m_id = %s"
		tuple = (query.message.chat_id, query.message.message_id)
		cur = db.tquery(sql, tuple)
		sql = cur.fetchall()
		gameId = sql[0][0]
		adminId = sql[0][1]
		theGame = sql[0][2]

		if query.data == '1':
			isMember = True
			for i in range(0, len(theMessage)):
				if theMessage[i:i+len(theUser.first_name)+2] == "- "+theUser.first_name:
					theMessage = theMessage[0:i-1]+theMessage[i+len(theUser.first_name)+3:len(theMessage)]
					sql = "DELETE FROM game_user WHERE g_id = %s AND u_id = %s"
					tuple = (gameId, theUser.id)
					cur = db.tquery(sql, tuple)
	                        	db.commit()
	                        	bot.edit_message_text(text=theMessage, chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=reply_markup)
					isMember = False
					break

			if isMember:
				sql = "INSERT INTO game_user (gu_id, g_id, u_id) VALUES (NULL, %s, %s)"
				tuple = (gameId, theUser.id)
				cur = db.tquery(sql, tuple)
				db.commit()
				bot.edit_message_text(text=theMessage+"\n - "+theUser.first_name, chat_id=query.message.chat_id, message_id=query.message.message_id, reply_markup=reply_markup)

		elif query.data == '2':
			if adminId == theUser.id:
				cur = db.tquery("SELECT u_id FROM game_user WHERE g_id = (SELECT g_id FROM game WHERE g_id = %s)", (gameId,))
				GameUser = cur.fetchall()
				theChat = []
				for i in range(len(GameUser)):
					cur = db.tquery("SELECT c_id FROM chat WHERE u_id = (SELECT u_id FROM user WHERE u_id = %s)", (GameUser[i][0],))
					theChat.append(cur.fetchall()[0][0])

				if len(theChat) > 2:
					rtd(bot, theChat, theGame)
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

		                        bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id)
				else:
					bot.send_message(chat_id=query.message.chat_id, text="I'm Sorry, this game does only make sense with 3 or more Players")

			else:
				cur = db.tquery("SELECT m_id FROM game WHERE g_id = %s", (gameId,))
				theMessage = cur.fetchall()[0][0]
				bot.send_message(chat_id=query.message.chat_id, reply_to_message_id=theMessage, text="Sorry "+(" " if theUser.first_name == None else theUser.first_name)+" "+("" if theUser.last_name == None else theUser.last_name)+", but you are not Admin of this game!")

		elif query.data == '3':
			if adminId == theUser.id:
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

				bot.edit_message_text(chat_id=query.message.chat_id, text=theMessage, message_id=query.message.message_id)
			else:
				cur = db.tquery("SELECT m_id FROM game WHERE g_id = %s", (gameId,))
        	                theMessage = cur.fetchall()[0][0]
        	                bot.send_message(chat_id=query.message.chat_id, reply_to_message_id=theMessage, text="Sorry "+(" " if theUser.first_name == None else theUser.first_name)+("" if theUser.last_name == None else theUser.last_name)+", but you are not Admin of this game!")

def initgame(bot, update, gName):
       	cur = db.tquery("INSERT INTO game (g_id, c_id, m_id, name, admin) VALUES (NULL, %s, %s, %s, %s)", (update.message.chat_id, update.message.message_id+1, gName, update.message.from_user.id))
        db.commit()
        bot.send_message(chat_id=update.message.chat_id, text=gName+"\nstatus: waiting for players!\nadmin: "+("" if update.message.from_user.first_name == None else update.message.from_user.first_name)+" "+("" if update.message.from_user.last_name == None else update.message.from_user.last_name)+"\n|\nmembers:\n", reply_markup=inlineKey())

def reply(bot, update):
	if update.message.chat_id in gcreate:
		initgame(bot, update, update.message.text)
		gcreate.remove(update.message.chat_id)

	if update.message.chat_id in feed:
		bot.send_message(chat_id=update.message.chat_id, text="Thank you for your feedback, I appreciate your time and thank you for using the bot.")
		feed.remove(update.message.chat_id)

	if update.message.chat_id in bug:
		bot.send_message(chat_id=update.message.chat_id, text="Thank you for reporting the bug, I will try to fix this as soon as possible.")
		bug.remove(update.message.chat_id)

def gamerules(bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="Rules:\nFirstly add me to a group.\nSecondly type in '/creategame [gamename]'.\nThirdly all users that want to play with you have to start a privat chat with me, then click the 'Join' button.\nAt the End the user who created the game (the admin) has to click 'Start'.\n\nOnce the game is started, each user gets a privat message from me with the randomly chosen player, the user has to get a gift for.")

def help(bot, update):
	update.message.reply_text("Commandlist:\n/start - for starting a conversation with MCSecretSantaBot\n/gamerules - for displaying the rules of the game\n/creategame [game name] - for creating a new game\n/help - for this help message\n/feedback - for improving the bot experience\n/bugreport - for reporting bugs")

def feedback(update, context):
	reply_markup = ForceReply(selective=True)
	context.bot.send_message(chat_id=update.message.chat_id, text="Please type in the Feedback", reply_markup=reply_markup)
	feed.append(update.message.chat_id)

def bugreport(update, context):
	reply_markup = ForceReply(selective=True)
	context.bot.send_message(chat_id=update.message.chat_id, text="Please type in the Bugreport", reply_markup=reply_markup)
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
