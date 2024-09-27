# (c) EDM115 - 2022

import os
import logging
from asyncio import sleep
from datetime import datetime, timedelta

from pyrogram import Client, enums, filters
from pyrogram.types import BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, RPCError

from config import *

# Define a list of authorized user IDs (you and sudo users)
AUTHORIZED_USERS = [your_user_id, sudo_user_id_1, sudo_user_id_2]  # Replace with your and your sudo users' actual IDs

banbot = Client(
    "banbot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    sleep_threshold=10
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler('logs.txt'), logging.StreamHandler()],
    format="%(asctime)s - %(levelname)s - %(name)s - %(threadName)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARN)

# Security check function
async def is_authorized_user(user_id: int) -> bool:
    """ Check if the user is authorized to use the bot """
    return user_id in AUTHORIZED_USERS

@banbot.on_message(filters.command("start"))
async def start_bot(_, message: Message):
    if await is_authorized_user(message.from_user.id):
        await message.reply_text(text="**Hello {} 👋**".format(message.from_user.mention), disable_web_page_preview=True)
    else:
        await message.reply_text("You are not authorized!!")

@banbot.on_message(filters.command("log"))
async def send_logs(_, message: Message):
    if await is_authorized_user(message.from_user.id):
        with open('logs.txt', 'rb') as doc_f:
            try:
                await banbot.send_document(
                    chat_id=message.chat.id,
                    document=doc_f,
                    file_name=doc_f.name,
                    reply_to_message_id=message.id
                )
                LOGGER.info(f"Log file sent to {message.from_user.id}")
            except FloodWait as e:
                await sleep(e.x)
            except RPCError as e:
                await message.reply_text(e, quote=True)
                LOGGER.warning(f"Error in /log : {e}")
    else:
        await message.reply_text("You are not authorized!!")

@banbot.on_message(filters.command("help"))
async def help_me(_, message: Message):
    if await is_authorized_user(message.from_user.id):
        await message.reply_text(text="""\
Here is the help :

--Preconditions :--
    • Be an admin
    • Have "Ban members" rights
    • Same conditions for me, the bot

--Usage :--
    • Send `/fusrodah`
    • Choose if you want to **Ban** or **Kick all** the members excepting the admins
    • Let the bot do its job
    • If some errors happened, check the errors text file to manually ban/kick those users ID's

--Help :--
    You can contact the support here : **@EDM115_chat**
    Subscribe for more : **@EDM115bots**
    Source code : https://github.com/EDM115/ban-all-except-admins
    """)
    else:
        await message.reply_text("You are not authorized!!")

@banbot.on_callback_query()
async def callbacks(banbot: Client, query: CallbackQuery):
    if await is_authorized_user(query.from_user.id):
        cid = query.message.chat.id
        uid = query.from_user.id
        qid = query.message.id

        # Retrieve admin list here
        adminlist = []
        async for admin in banbot.get_chat_members(chat_id=cid, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            adminlist.append(admin)

        if query.data == "nope":
            return await query.edit_message_text("❌ Successfully canceled your task ✅")
        elif query.data == "kick":
            await justdoit("Kicking", 0, cid, uid, qid, adminlist)
        elif query.data == "ban":
            await justdoit("Banning", 1, cid, uid, qid, adminlist)
    else:
        await query.answer("You are not authorized!!", show_alert=True)

@banbot.on_message(filters.command("fusrodah"))
async def being_devil(_, message: Message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        starter = message.from_user.id
        if await is_authorized_user(starter):
            cid = message.chat.id
            LOGGER.info(f"{starter} started a task in {cid}")

            adminlist = []
            async for admin in banbot.get_chat_members(chat_id=cid, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                adminlist.append(admin)

            if starter in [admin.user.id for admin in adminlist]:
                admin = adminlist[0]
                if admin.privileges.can_restrict_members:
                    botid = int(Config.BOT_TOKEN.split(":")[0])
                    selfuser = await banbot.get_chat_member(chat_id=cid, user_id=botid)
                    if selfuser.privileges.can_restrict_members:
                        await message.reply("Confirm your action:\n• Kick all members except admins\n• **Ban** all members except admins\n• Cancel", reply_markup=Buttons.CONFIRMATION)
                    else:
                        LOGGER.warning("Bot cannot ban members")
                        await message.reply("The bot needs the 'Ban Members' permission to proceed.")
                else:
                    LOGGER.warning("User cannot ban members")
                    await message.reply("You don't have the necessary 'Ban Members' permission.")
            else:
                LOGGER.warning("Not admin")
                await message.reply("You're not an admin.")
        else:
            await message.reply("You are not authorized!!")
    else:
        LOGGER.warning("Not in group")
        await message.reply("This command must be used in a group.")

LOGGER.info("Bot started")
banbot.run()
