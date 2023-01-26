import telegram
from functions import month_converter
from functions import *
import logging
import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ApplicationHandlerStop,
    CommandHandler,
    InvalidCallbackData,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

PORT = int(os.environ.get('PORT', '8443'))
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
print()
name = ''

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

ACTION, FINISH = range(2)
DOWNLOAD, DETAILS, = range(2)

ONE, TWO = range(2)
START_ROUTES, END_ROUTES = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        await update.message.reply_text(
            'Welcome To Terader Movie Hub the place where movie links meet!..../usage if you are having issues.')
    except RuntimeError:
        await update.message.reply_text(
            'Welcome To Terader Movie Hub the place where movie links meet!..../usage if you are having issues.')


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = context.bot
    chat = chat.getChatMember(user_id=update.effective_user.id, chat_id='@teradermoviehub')
    result = await chat
    if result.status == 'left':
        await update.message.reply_text('You have to be on the telegram channel first!')
        await update.message.reply_text(parse_mode='HTML', text='https://t.me/teradermoviehub')
        raise ApplicationHandlerStop


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    id = update.effective_message.text[3:]
    if update.effective_message.text[1:3] == 'm_':
        category = 'movie'
    else:
        category = 'tv'
    req = requests.get(
        f'https://api.themoviedb.org/3/{category}/{id}?api_key={os.environ.get("api_key")}&append_to_response=videos')
    req = req.json()
    if req:
        if category == 'movie':
            caption = f'🎬Title: {req["title"]}\n 🎯Released: {req["release_date"]}\nOverview: {req["overview"]}\nIMDB LINK: https://www.imdb.com/title/{req["imdb_id"]}\nVoted: {req["vote_average"]}\nTagline: {req["tagline"]}\n'
            genre = ''
            if req['genres']:
                genres = req['genres']
                for items in genres:
                    genre += items['name'] + ','
            try:
                photo = f'https://image.tmdb.org/t/p/w500/{req["poster_path"]}'
                await update.effective_message.reply_photo(photo=photo, caption=f'{caption} 🎭Genres: {genre}')
            except Exception:
                await update.effective_message.reply_text(text=f'{caption} 🎭Genres: {genre}')
            title = req['title'].replace(':', '')
            title = title[:50]
            keyboard = [
                [InlineKeyboardButton(text='DOWNLOAD', callback_data=str('o' + title))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await update.message.reply_text(text='DOWNLOAD LINKS', reply_markup=reply_markup)
        else:
            caption = f'🎬Title: {req["name"]}\n 🎯Released: {req["first_air_date"]}\nOverview: {req["overview"]}\nVoted: {req["vote_average"]}\nTagline: {req["tagline"]}\n'
            genre = ''
            if req['genres']:
                genres = req['genres']
                for items in genres:
                    genre += items['name'] + ','
            try:
                photo = f'https://image.tmdb.org/t/p/w500/{req["poster_path"]}'
                await update.message.reply_photo(photo=photo, caption=f'{caption} 🎭Genres: {genre}')
            except Exception:
                await update.message.reply_text(text=f'{caption} 🎭Genres: {genre}')
            keyboard = [
                [
                    InlineKeyboardButton("DOWNLOAD", callback_data=f'{"t" + req["name"]}'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await update.message.reply_text(text='DOWNLOAD LINKS', reply_markup=reply_markup)
    return START_ROUTES


async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton(text='Movie', callback_data=str('movie' + update.effective_message.text.lower())),
            InlineKeyboardButton(text='Series', callback_data=str('series' + update.effective_message.text.lower()))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        text=f'Is {update.effective_message.text} a Movie Or a Series. Select One..',
        reply_markup=reply_markup)


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please request for the item again."
    )


async def search_item(update: Update, message) -> None:
    query = update.callback_query
    await query.answer()
    query.data = query.data.lower()
    if 'movie' in query.data.lower():
        query = query.data[5:]
        await update.callback_query.message.edit_text(f"Showing Search results for {query}")
        req = search(query, category='movie', results=False, page=False)
        if req:
            for items in req:
                link = items['id']
                released = ''
                try:
                    released = month_converter(items['release_date'])
                except KeyError:
                    released = 'NULL'
                photo = items["poster_path"]
                try:
                    photo = f'https://image.tmdb.org/t/p/w500/{photo}'
                    await update.callback_query.message.reply_photo(photo=photo,
                                                                    caption=f"🎬Title: {items['title']}\n📃Click to view: /m_{link}\n🔤Language: {items['original_language']}\n🎯Released: {released}\n✅Voted: {items['vote_average']}")
                except telegram.error.BadRequest:
                    await update.callback_query.message.reply_text(
                        'Sorry no Photo Available for this movie so use the release date to determine if this is your search item')
                    await update.callback_query.message.reply_text(
                        text=f"🎬Title: {items['title']}\n📃Click to view: /m_{link}\n🔤Language: {items['original_language']}\n🎯Released: {released}\n✅Voted: {items['vote_average']}")
        else:
            await update.callback_query.message.reply_text(
                f'No results for {query} was found...are you sure you typed the correct thing? Please refer to /usage')
    elif 'series' in query.data:
        await update.callback_query.message.edit_text(f"Showing Search results for series with name: {query.data[6:]}")
        query = query.data[6:]
        req = search(query, category='tv', results=False, page=False)
        if req:
            for items in req:
                link = items['id']
                try:
                    first_air_date = month_converter(items['first_air_date'])
                except KeyError:
                    first_air_date = 'NULL'
                photo = items['poster_path']
                photo = f'https://image.tmdb.org/t/p/w500/{photo}'
                try:
                    await update.callback_query.message.reply_photo(photo=photo,
                                                                    caption=f"🎬Name: {items['name']}\n📃Click to view: /s_{link}\n🔤Language: {items['original_language']}\n🎯Released: {first_air_date}\n✅Voted: {items['vote_average']}")
                except telegram.error.BadRequest:
                    await update.callback_query.message.reply_text(
                        'Sorry no Photo Available for this series so please use the first air date to determine if this is your search item')
                    await update.callback_query.message.reply_text(
                        text=f"🎬Name: {items['name']}\n📃Click to view: /s_{link}\n🔤Language: {items['original_language']}\n🎯First Air Date: {first_air_date}\n✅Voted: {items['vote_average']}")
        else:
            await update.callback_query.message.reply_text(
                f'No results for {query} was found...are you sure you typed the correct thing? Please refer to /usage')
    else:
        await update.callback_query.message.reply_text(
            '☹This is not a valid command check /usage to know how to use this bot')


async def one(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    data = query.data[1:]
    await query.answer()
    if query.data[0] == 'o':
        await query.edit_message_text('Connecting to the database....')
        title = data.lower()
        keyboard = []
        link3 = netnaija(title)
        if link3:
            await query.edit_message_text('Connecting To database...')
            length = len(link3)
            for links in range(0, length):
                if links % 2 != 0:
                    keyboard.append(
                        [
                            InlineKeyboardButton(f"{link3[links - 1]}", callback_data=str(ONE), url=link3[links])
                        ]
                    )
        link4 = search_torrent1337x(title)
        if link4:
            await query.edit_message_text('Getting torrents....')
            keyboard.append(
                [InlineKeyboardButton(text='Torrent downloader for windows',
                                      url='https://www.utorrent.com/downloads/win/')],
            )
            keyboard.append(
                [InlineKeyboardButton(text='Torrent downloader for mac',
                                      url='https://www.utorrent.com/downloads/complete/track/stable/os/mac/')],
            )
            keyboard.append(
                [InlineKeyboardButton(text='Torrent downloader for android',
                                      url='https://play.google.com/store/apps/details?id=com.utorrent.client&hl=en_CA&gl=US')],
            )
            length = len(link4)
            link_count = 0
            for links in range(0, length):
                keyboard.append(
                    [
                        InlineKeyboardButton(f"TORRENT LINK", callback_data=str(ONE), url=link4[links])
                    ]
                )
                if link_count > 4:
                    break
        reply_markup = InlineKeyboardMarkup(keyboard)
        for i in tfpd('mo', title.lower()):
            if isinstance(i, list):
                link = i
                break
            elif isinstance(i, int):
                await query.edit_message_text(text=f'Connecting.....{str(i)}%')
                if i == 100:
                    await query.edit_message_text(text=f'Collecting data....')
            else:
                await query.edit_message_text(text=f'{i}')
        if link:
            await query.edit_message_text('Connected...')
            for links in range(0, (len(link))):
                if links % 2 != 0:
                    keyboard.append(
                        [
                            InlineKeyboardButton(f"{link[links - 1]}", callback_data=str(ONE), url=link[links])
                        ]
                    )
        keyboard.append([InlineKeyboardButton(f'Complaints?..Click here to chat with admin', url='https://t.me/teraderr')
        ])
        if len(keyboard) == 1:
            await query.edit_message_text('Links Not Found')
        else:
            await query.edit_message_text('Click any to download', reply_markup=reply_markup)
    else:
        title = data.lower()
        await query.edit_message_text('This is a series so make sure you have a strong internet connection')
        keyboard = []
        link4 = search_torrent1337x('se' + title.lower())
        for i in tfpd('se', title.lower()):
            if isinstance(i, list):
                link = i
                break
            elif isinstance(i, int):
                await query.edit_message_text(text=f'Loading.....{str(i)}%')
                if i == 100:
                    await query.edit_message_text(text=f'Collecting data....')
            else:
                await query.edit_message_text(text=f'{i}')
        if link:
            await query.edit_message_text('Connected...')
            for links in range(0, (len(link))):
                if len(keyboard) > 25:
                    del (keyboard[25:])
                    break
                if links % 2 != 0:
                    keyboard.append(
                        [
                            InlineKeyboardButton(f"{link[links - 1]}", callback_data=str(ONE), url=link[links])
                        ]
                    )

        if link4:
            await query.edit_message_text('Getting torrents....')
            length = len(link4)
            for links in range(0, length):
                if len(keyboard) > 15:
                    break
                keyboard.append(
                    [
                        InlineKeyboardButton(f"TORRENT LINK", callback_data=str(ONE), url=link4[links])
                    ]
                )
        link3 = netnaija(title)
        if link3:
            await query.edit_message_text('Secure database connection...')
            length = len(link3)
            for links in range(0, length):
                if len(keyboard) > 15:
                    break
                if links % 2 != 0:
                    keyboard.append(
                        [
                            InlineKeyboardButton(f"{link3[links - 1]}", callback_data=str(ONE), url=link3[links])
                        ]
                    )
        if len(keyboard) > 25:
            del (keyboard[25:])
        keyboard.append([InlineKeyboardButton(f'Complaints?..Click here to chat with admin', url='https://t.me/teraderr')
                         ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        if len(keyboard) == 0:
            await query.edit_message_text('Links Not Found')
        else:
            await query.edit_message_text('Click to download', reply_markup=reply_markup)
    return START_ROUTES


async def two(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer('We dont have this item in the database', show_alert=True)
    return START_ROUTES


async def upcoming(update, context):
    await update.message.reply_text('1.More Movie and series support for richer links and wider range of movies!')


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        'If you have any issues or complaints message admin @teraderr for any issues')


async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Step 1:Type the name of your search eg the witcher\n'
        'Step 2: Select the category after\n '
        'Step 3: If item is found select your item from the search results tap on the "click to view movie"\n'
        'Step 4:If you wish to download click on the download button\n'
        'Step 5: Click on the downloads links if available'
    )


async def disclaimer(update, context):
    await update.message.reply_text(
        'NOTE:DOWNLOAD LINKS ARE NOT ACCURATE AND ARE NOT PART OF THE DATABASE THEY BELONG '
        'TO OTHER WEBSITES!\n WE OWE NO RESPONSIBILITY TO INAPPROPRIATE CONTENTS!')


async def help(update, message):
    await update.message.reply_text(
        "If you click on a download link and it  takes you to a page with the title"
        " xxprox... just complete the recaptcha by clicking 'i am not a robot' after the"
        " 'verify that you are a human text' and your download should start promptly ")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_error_handler(error)
    con_hand = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"[_]+[0-9]+"), movie)],

        states={
            START_ROUTES: [
                CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(r'[_]+[0-9]+'), movie)],
    )
    handler = telegram.ext.TypeHandler(Update, callback)  # Making a handler for the type Update
    application.add_handler(handler, -1)
    application.add_handler(CallbackQueryHandler(one, pattern="^" + r'[o]' + "+"))
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(two, pattern="^" + str(ONE) + "$"))
    application.add_handler(CallbackQueryHandler(search_item, pattern='^' + r"[movie]|[series]" + "+"))
    application.add_handler(CallbackQueryHandler(one, pattern="^" + r'[t]' + '+'))
    application.add_handler(MessageHandler(filters.Regex(r"[_]+[0-9]+"), movie))
    application.add_handler(CommandHandler('disclaimer', disclaimer))
    application.add_handler(CommandHandler('usage', usage))
    application.add_handler((CommandHandler('start', start)))
    application.add_handler(CommandHandler('upcoming', upcoming))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(MessageHandler(filters.TEXT, get_type))
    application.add_handler(con_hand)
    application.run_polling()



if __name__ == '__main__':
    main()
