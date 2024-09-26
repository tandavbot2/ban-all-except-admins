# (c) EDM115 - 2022

import os
import logging
from asyncio import sleep
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from asyncio import sleep, TimeoutError
from pyrogram.errors import FloodWait

from pyrogram import Client, enums, filters
from pyrogram.types import BotCommand, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, RPCError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import *

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

@banbot.on_message(filters.command("start"))
async def start_bot(_, message: Message):
    await message.reply_text(text="**Hello {} 👋**".format(message.from_user.mention), disable_web_page_preview=True)

@banbot.on_message(filters.command("log"))
async def send_logs(_, message: Message):
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

@banbot.on_message(filters.command("help"))
async def help_me(_, message: Message):
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

class Buttons:
    CONFIRMATION = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Kick 🚪", callback_data="kick"),
            InlineKeyboardButton("Ban 🕳", callback_data="ban")
        ],
        [
            InlineKeyboardButton("Cancel ❌", callback_data="nope")
        ]
    ])

class Text:
    PROCESSING = """\
Retrieving members of the chat… {}
Comparing with the admins of the chat… {}
{} members… {}/{} ({} errors)
    """

@banbot.on_callback_query()
async def callbacks(banbot: Client, query: CallbackQuery):
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

async def justdoit(text, mode, chat, user, query, adminlist):
    await banbot.delete_messages(chat_id=chat, message_ids=query)
    memberslist = []
    action = await banbot.send_message(chat_id=chat, text="`Processing… ⏳`")
    
    try:
        await action.edit(Text.PROCESSING.format("⏳", "⏳", text, 0, 0, 0))

        batch_size = 15
        total_retrieved = 0
        
        # Retrieve chat members with batching
        async for member in banbot.get_chat_members(chat_id=chat):
            memberslist.append(member)
            total_retrieved += 1
            
            # Log every 50 members retrieved
            if total_retrieved % 50 == 0:
                logger.info(f"Retrieved {total_retrieved} members so far.")

            # Update the message every 200 members
            if total_retrieved % 200 == 0:
                await action.edit(Text.PROCESSING.format(f"{len(memberslist)} members found", "⏳", text, 0, 0, 0))

            # Wait for the batch size to reach before continuing
            if len(memberslist) >= batch_size:
                await sleep(5)  # Wait for 5 seconds before the next batch
                memberslist = []  # Reset the list for the next batch

        # After retrieval, continue with the kicking logic
        memberslist = [member for member in memberslist if member not in adminlist]

        actioncount = len(memberslist)
        donecount = 0
        errorcount = 0
        errorlist = []

        await action.edit(Text.PROCESSING.format(total_retrieved, "Done ✅", text, donecount, actioncount, errorcount))

        for member in memberslist:
            try:
                useraction = member.user.id
                if mode == 0:
                    await banbot.ban_chat_member(chat_id=chat, user_id=useraction, until_date=datetime.now() + timedelta(seconds=31))
                elif mode == 1:
                    await banbot.ban_chat_member(chat_id=chat, user_id=useraction)

                donecount += 1

            except FloodWait as f:
                logger.warning(f"Flood wait: {f.x} seconds. Waiting...")
                await sleep(f.x)  # Wait for the specified flood wait time
            except Exception as e:
                logger.error(f"Error processing user {useraction}: {e}")
                errorcount += 1
                errorlist.append(useraction)

            # Update progress after each action
            await action.edit(Text.PROCESSING.format(total_retrieved, "Done ✅", text, donecount, actioncount, errorcount))
            await sleep(5)  # Adjust this delay to help manage flood control

    except TimeoutError:
        logger.error("Operation timed out while processing members.")
    except Exception as e:
        logger.error(f"Error in justdoit: {e}")

@banbot.on_message(filters.command("fusrodah"))  # & filters.group
async def being_devil(_, message: Message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        starter = message.from_user.id
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
        LOGGER.warning("Not in group")
        await message.reply("This command must be used in a group.")

LOGGER.info("Bot started")
banbot.run()
