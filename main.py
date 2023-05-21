import uuid
import telegram
from telegram.constants import ChatAction
from utils import *
import logging
import os
import requests
from web_scrappers.netnaija import netnaija_web_scrapper
from web_scrappers.tfpdl import tfpdl
from web_scrappers.torrent_1337x import search_torrent1337x
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
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

api_key = os.environ.get('tmdbApiKey')
PORT = int(os.environ.get('PORT', '8443'))
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
name = ''

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

ACTION, FINISH = range(2)
DOWNLOAD, DETAILS, = range(2)

ONE, TWO = range(2)
START_ROUTES, END_ROUTES = range(2)
# Callback data
THREE, FOUR = range(4)

ResultsCache = {}
ResultsPerPage = 1

LinksCache = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Welcome To Terader Movie Hub the place where movie links meet!..../usage if you are having issues.')


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if the user belongs to the telegram group"""
    chat = context.bot
    chat = chat.getChatMember(user_id=update.effective_user.id, chat_id='@teradermoviehub')
    result = await chat
    if result.status == 'left':
        await update.message.reply_text('You have to be on the telegram channel first!')
        await update.message.reply_text(parse_mode='HTML', text='https://t.me/teradermoviehub')
        raise ApplicationHandlerStop


async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Pagination requests"""
    query = update.callback_query
    data = query.data

    user_id = query.message.chat_id
    pagination_id, page = data.split('-')[1].split(':')

    # check if the callback is valid
    if page == 0:
        return

    # Check if the results for the current page are already in the cache
    cache_key = ResultsCache.get(user_id, None)

    if cache_key:
        results = cache_key.get(pagination_id)
        if not results:
            # the user has a list of movies but this current one is old/deleted
            await query.answer(text="Message Expired\nPlease resend request", show_alert=True)
            return
        results = results[0]
        pages_length = int(len(results))
        results = results.get(page)

        # answer the callback
        await query.answer()
    else:
        # the user doesn't have any list of movies probably the server restarted
        await query.answer(text="Message Expired\nPlease resend request", show_alert=True)
        return

    page = int(page)

    # Create a list of button labels for the pagination buttons
    button_labels = []
    if page > 1:
        button_labels.append('<< Prev')

    button_labels.append('🗒 {}/{}'.format(page, pages_length))

    # check if the search results are more
    if pages_length > page:
        button_labels.append('Next >>')

    # Create the pagination buttons using InlineKeyboardButton
    buttons = []
    for label in button_labels:
        if label == '<< Prev':
            buttons.append(telegram.InlineKeyboardButton(text=label,
                                                         callback_data='page-{}:{}'.format(pagination_id, page-1)))
        elif label == 'Next >>':
            buttons.append(telegram.InlineKeyboardButton(text=label,
                                                         callback_data='page-{}:{}'.format(pagination_id, page+1)))
        else:
            buttons.append(telegram.InlineKeyboardButton(text=label,
                                                         callback_data='page-{}:0'.format(pagination_id)))

    # Create an InlineKeyboardMarkup object with the pagination buttons
    reply_markup = telegram.InlineKeyboardMarkup([buttons])

    movie_poster_url = f'https://image.tmdb.org/t/p/w500{results["poster_path"]}'
    file_obj = await get_raw_image(movie_poster_url)

    # title_key might be saved as either name or title
    if results.get('title'):
        title_key = 'title'
        release_date_key = 'release_date'
    else:
        title_key = 'name'
        release_date_key = 'first_air_date'

    link_prefix = 'm' if title_key == 'title' else 's'
    link = '/{}_{}'.format(link_prefix, results['id'])

    movie_caption = f"🎬Title: {results[title_key]}\n " \
                    f"📃Click to view: {link}\n " \
                    f"🔤Language: {results['original_language']}\n " \
                    f"🎯Released: {month_converter(results[release_date_key])}\n" \
                    f" ✅Voted: {results['vote_average']}"

    # check if the file was gotten and converted to an image in the case of movies that don't have pictures
    if file_obj:
        await update.effective_user.send_chat_action(action=ChatAction.UPLOAD_PHOTO)
        # Send the current page of results to the user with the pagination buttons
        photo = InputMediaPhoto(media=file_obj, caption=movie_caption)
        try:
            # this would occur when the button is pressed more than once so the new content and old content
            # would not change throws a telegram.error.BadRequest: Message is not modified: specified new
            # message content and reply markup are exactly the same as a current content and reply markup
            # of the message
            await update.effective_message.edit_media(media=photo, reply_markup=reply_markup)
        except telegram.error.BadRequest:
            pass
    else:
        await update.effective_user.send_chat_action(action=ChatAction.TYPING)
        await update.effective_message.edit_caption(caption=movie_caption, reply_markup=reply_markup)


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fetches the movie gotten from the callback"""
    category, movie_id = update.effective_message.text.split('_')
    category = "movie" if category == '/m' else "tv"

    req = requests.get(
        f'https://api.themoviedb.org/3/{category}/{id}?api_key={api_key}')

    if req.status_code == 200:
        req = req.json()
        # get the image for the movie
        movie_poster_url = f'https://image.tmdb.org/t/p/w500{req["poster_path"]}'
        file_obj = await get_raw_image(movie_poster_url)

        imdb_link = f'IMDB LINK: https://www.imdb.com/title/{req["imdb_id"]}\n' if req.get("imdb_id") else ''

        # the result gotten from the api can have either a title key or a name key
        # based on if the request is a movie or series
        title_key, release_date_key = get_movie_type(req)
        caption = f'🎬Title: {req.get(title_key)}\n' \
                  f' 🎯Released: {req.get(release_date_key)}\n' \
                  f'Overview: {req.get("overview")[:200]}\n' \
                  f' {imdb_link}' \
                  f' Voted: {req.get("vote_average")}\n' \
                  f'Tagline: {req.get("tagline")}\n'

        genre = ''
        # join the genres together
        if req.get('genres'):
            genre += ','.join([items['name'] for index, items in enumerate(req['genres']) if index < 6])

        # check if the photo was converted successfully
        if file_obj:
            await update.effective_user.send_chat_action(action=ChatAction.UPLOAD_PHOTO)
            await update.effective_message.reply_photo(photo=file_obj, caption=f'{caption} 🎭Genres: {genre}')
        else:
            await update.effective_user.send_chat_action(action=ChatAction.TYPING)
            await update.effective_message.reply_text(text=f'{caption} 🎭Genres: {genre}')

        title = req.get(title_key)
        # slice the tile if it's too long
        title = title[:50]
        callback_prefix = f'download_movie_{title}' if category == 'movie' else f'download_series_{title}'
        keyboard = [
            [
                InlineKeyboardButton(text='DOWNLOAD', callback_data=callback_prefix)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.message.reply_text(text='DOWNLOAD LINKS', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text="The requested resource could not be found")
    return START_ROUTES


async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the type of movie that the user searched for
    """
    keyboard = [
        [
            InlineKeyboardButton(text='Movie', callback_data=str('movie: ' + update.effective_message.text.lower())),
            InlineKeyboardButton(text='Series', callback_data=str('series: ' + update.effective_message.text.lower()))
        ]
    ]
    await update.effective_user.send_chat_action(action=ChatAction.TYPING)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        text=f'Is {update.effective_message.text} a Movie Or a Series. Select One..',
        reply_markup=reply_markup)


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.effective_user.send_chat_action(action=ChatAction.TYPING)
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please request for the item again."
    )


async def search_item(update: Update, message) -> None:
    """Searches for the movie requested"""
    query = update.callback_query
    await query.answer()
    await update.effective_user.send_chat_action(action=ChatAction.TYPING)

    movie_name = query.data.split(':')[1]
    await update.callback_query.message.edit_text(f"Showing Search results for {movie_name}")

    # get the request type
    category = 'movie' if 'movie' in query.data.lower() else 'tv'

    # call the search function to search and return the movie
    req = await search(movie_name, category=category)

    req_cols = ['overview', 'original_language', 'vote_average', 'id', 'poster_path', 'backdrop_path']

    if req:
        # send the first message with the pagination links
        item = req[0]

        # the result gotten from the api can have either a title as a key or a name as a key
        # depending on if it is a movie or series
        if category == 'movie':
            title_key = 'title'
            # append the release_date and title_key property
            # so that the pagination can be saved with this property
            req_cols.append('release_date')
        else:
            title_key = 'name'
            req_cols.append('first_air_date')
        req_cols.append(title_key)

        # get the image for the movie
        movie_poster_url = f'https://image.tmdb.org/t/p/w500{item["poster_path"]}'
        file_obj = await get_raw_image(movie_poster_url=movie_poster_url)

        # generate a new UUID
        unique_id = uuid.uuid4()

        # convert the UUID to a string
        unique_id_str = str(unique_id)[:4]

        if len(req) > 1:
            keyboard = [
                [
                    InlineKeyboardButton(text=f'🗒 1 / {len(req)}',
                                         callback_data="-----"),
                    InlineKeyboardButton(text='Next>>',
                                         callback_data='page-{}:2'.format(unique_id_str))
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(text=f'🗒 1',
                                         callback_data="-----"),
                ]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        released = 'release_date' if item.get('release_date', None) else 'first_air_date'
        link_prefix = 'm' if title_key == 'title' else 's'
        link = '/{}_{}'.format(link_prefix, item['id'])
        movie_caption = f"🎬Title: {item[title_key]}\n " \
                        f"📃Click to view: {link}\n " \
                        f"🔤Language: {item['original_language']}\n " \
                        f"🎯Released: {item[released]}\n" \
                        f" ✅Voted: {item['vote_average']}"
        try:
            await update.effective_user.send_chat_action(action=ChatAction.UPLOAD_PHOTO)
            await update.callback_query.message.reply_photo(photo=file_obj,
                                                            caption=movie_caption,
                                                            reply_markup=reply_markup)

        except telegram.error.BadRequest:
            await update.callback_query.message.reply_text(
                'Sorry no Photo Available for this movie so use'
                ' the release date to determine if this is your search item')
            await update.callback_query.message.reply_text(
                text=movie_caption,
                reply_markup=reply_markup
            )

        # check if the user already has a list of pagination's
        userItems = ResultsCache.get(update.effective_message.chat_id, None)
        if userItems:
            length = len(userItems)
            if length >= 3:
                # delete the first item in the  dictionary
                dict_key = list(userItems.keys())[0]
                userItems.pop(dict_key)
            # save the results and update the user's list for easy pagination
            ResultsCache[update.effective_message.chat_id].update(
                {unique_id_str:  [{f'{index + 1}': {key: movie_item[key] for key in req_cols}
                                   for index, movie_item in enumerate(req)}]}
            )
        else:
            # save the results for easy pagination
            ResultsCache[update.effective_message.chat_id] = {
                unique_id_str: [{f'{index + 1}': {key: movie_item[key] for key in req_cols}
                                for index, movie_item in enumerate(req)}]
            }

    else:
        await update.callback_query.message.reply_text(
            f'No results for {query.data}, was found...are you sure you typed the correct thing?'
            f' Please refer to /usage')


async def download_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()

    download_type, title = query.data.split('_')[1:]

    if download_type == 'series':
        await update.effective_user.send_chat_action(action=ChatAction.TYPING)
        await query.edit_message_text('This is a series so make sure you have a strong internet connection')

    await query.edit_message_text('Connecting to the database....')

    title = title.lower()
    keyboard = []

    link5 = tfpdl(download_type, title)
    # the tfpdl function is an async generator function
    if link5:
        async for item in link5:
            # loop through the list asynchronously
            if isinstance(item, list):
                # this is true if this is the actual fetched movie download link
                await query.edit_message_text('Connected...')
                for link in item:
                    keyboard.append(
                        [
                            InlineKeyboardButton(f"{link.get('title')}", callback_data=str(ONE), url=link.get('url'))
                        ]
                    )
                break

            elif isinstance(item, int):
                # if this is the progress of this scraping
                await query.edit_message_text(text=f'Connecting.....{str(item)}%')
                if item == 100:
                    await query.edit_message_text(text=f'Collecting data....')
            else:
                # function yields some information string
                await query.edit_message_text(text=f'{item}')

    await update.effective_user.send_chat_action(action=ChatAction.TYPING)
    link3 = await netnaija_web_scrapper(title)
    if link3:
        await query.edit_message_text('Connected To database...')
        for link in link3:
            keyboard.append(
                [
                    InlineKeyboardButton(text=link.get('text'), callback_data=str(ONE), url=link.get('url'))
                ]
            )

    link4 = await search_torrent1337x(movie_type=download_type, title=title)
    if link4:
        await query.edit_message_text('Getting torrents....')
        for index, link in enumerate(link4):
            keyboard.append(
                [
                    InlineKeyboardButton(text="TORRENT LINK", callback_data=str(ONE), url=link)
                ]
            )
            # we don't want unnecessary and repeated torrents
            if index > 3:
                break

    keyboard.append(
        [
            InlineKeyboardButton(f'Complaints?..Click here to chat with admin', url='https://t.me/teraderr')
         ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    if len(keyboard) <= 1:
        await query.edit_message_text('Links Not Found')
    else:
        await query.edit_message_text('Click any to download', reply_markup=reply_markup)
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


async def help_func(update, message):
    await update.message.reply_text(
        "If you click on a download link and it  takes you to a page with the title"
        " xxprox... just complete the recaptcha by clicking 'i am not a robot' after the"
        " 'verify that you are a human text' and your download should start promptly ")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    # Can test for different patterns using the '|' seperator
    # so to attach two patterns to one function you can write pattern1|pattern2
    application = Application.builder().token(TOKEN).build()
    application.add_error_handler(error)
    con_hand = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"[_]+[0-9]+"), movie)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(download_links, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(r'[_]+[0-9]+'), movie)],
    )
    handler = telegram.ext.TypeHandler(Update, callback)  # Making a handler for the type Update
    application.add_handler(handler, -1)
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"))
    application.add_handler(CallbackQueryHandler(search_item, pattern='^' + r"[movie]|[series]" + "+"))
    application.add_handler(CallbackQueryHandler(download_links, pattern="^" + '[download_movie_]|[download_series_]+'))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern="^" + 'page-' + '+'))
    application.add_handler(MessageHandler(filters.Regex(r"[_]+[0-9]+"), movie))
    application.add_handler(CommandHandler('disclaimer', disclaimer))
    application.add_handler(CommandHandler('usage', usage))
    application.add_handler((CommandHandler('start', start)))
    application.add_handler(CommandHandler('upcoming', upcoming))
    application.add_handler(CommandHandler('help', help_func))
    application.add_handler(MessageHandler(filters.TEXT, get_type))
    application.add_handler(con_hand)
    if os.environ.get('DEBUG', False):
        application.run_polling()
    else:
        application.run_webhook()


if __name__ == '__main__':
    main()
