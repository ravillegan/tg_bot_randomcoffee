from operator import length_hint
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
import motor.motor_asyncio
from datetime import datetime, timedelta
import random
from random import randint
import asyncio
import aioschedule
from aiogram.utils.exceptions import BotBlocked


#TOKEN = os.getenv('BOT_TOKEN')
TOKEN = "5442350518:AAECjitffl2ZMbwCf5UhOJwg7S2mFkzH8fk"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

cluster = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://raville_ganiev:07089910Rgu@cluster0.5giudi4.mongodb.net/?retryWrites=true&w=majority", tls=True, tlsAllowInvalidCertificates=True)
users_collection = cluster.randomcoffee.users
week_collection = cluster.randomcoffee.week
start_collection = cluster.randomcoffee.start_users
week_pairs_collection = cluster.randomcoffee.week_pairs
freetext_collection = cluster.randomcoffee.freetext

async def user_info(user_info_json):
    if hasattr(user_info_json, 'username') and user_info_json.username is not None:
        user_id = user_info_json.username
    elif hasattr(user_info_json, 'first_name') and hasattr(user_info_json, 'last_name') and user_info_json.first_name is not None and user_info_json.last_name is not None:
        user_id = ' '+user_info_json.first_name + ' ' + user_info_json.last_name
    elif hasattr(user_info_json, 'last_name') and user_info_json.last_name is not None:
        user_id = ' '+user_info_json.last_name
    elif hasattr(user_info_json, 'first_name') and user_info_json.first_name is not None:
        user_id = ' '+user_info_json.first_name
    else:
        user_id =' Таинственный собеседник ' +user_info_json.from_user.id
    return user_id

async def get_user_name(user_id):
    user_name_json = await week_collection.find_one({'user_id': str(user_id)})
    user_name = user_name_json['user_name']
    return user_name

async def add_user(user_id, user_name, community):
    if await users_collection.count_documents({'user_id': {'$eq': str(user_id)}}) != 0:
        return 'already'
    await users_collection.insert_one({'user_id': str(user_id), 'user_name' : user_name, 'first_community' : community})
    return 'new'

async def add_start(user_id, user_name):
    if await start_collection.count_documents({'user_id': {'$eq': str(user_id)}}) != 0:
        return 'already'
    await start_collection.insert_one({'user_id': str(user_id), 'user_name' : user_name})
    return 'new'

# async def update_user(user_id, user_name, city, community):
#     await users_collection.update_one({'user_id': str(user_id)}, {'$set': {'user_name': str(user_name), 'city': str(city), 'community': str(community)}})

async def want_to_coffee(user_id, user_name, community, week):
    await add_user(user_id, user_name, community)
    print(week)
    # if await week_collection.count_documents({'user_id': {'$eq': str(user_id)}, 'community': {'$eq': str(community)}, 'week': {'$eq': str(week)}}) != 0:
    if await week_collection.count_documents({'user_id': {'$eq': str(user_id)}, 'week': {'$eq': str(week)}}) != 0:
        return 'already'
    await week_collection.insert_one({'user_id': str(user_id), 'user_name' : user_name, 'community': str(community), 'week': str(week)})
    return 'new'

async def shuffle_week_pairs():
    coms = []
    today = datetime.now().date()
    async for docs in week_collection.find({'week':str(today)}):
        if docs['community'] not in coms:
            coms.append(docs['community'])
    number_of_coms = len(coms)
    pairs = [[] for i in range(number_of_coms)]
    i = 0
    for com in coms:
        async for docs in week_collection.find({'community': str(com), 'week':str(today)}):
            pairs[i].append(docs['user_id'])
        i += 1
    for i in range(number_of_coms):
        random.shuffle(pairs[i])
    return(pairs, coms)

async def create_week_pairs():
    pairs, coms = await shuffle_week_pairs()
    com_num = 0
    # now = datetime.now()
    # next_monday = (now - timedelta(days = now.weekday()) + timedelta(days=7)).date()
    today = datetime.now()
    next_friday = (today + timedelta( (4-today.weekday()) % 7 )).date()
    for com in pairs:
        if len(com) == 1:
            await bot.send_message(chat_id = int(com[0]), text = "К сожалению, из твоего комьюнити никто, кроме тебя, не принял участия на следующую неделю")
            await bot.send_message(chat_id = int(com[0]), text = "Помоги мне, напиши об этом в беседу, ведь мой создатель так старался 🥺")
            try:
                await week_pairs_collection.insert_one({'user_id_1': str(com[0]), 'user_name_1' : await get_user_name(int(com[0])), 'community': str(coms[com_num]), 'week': str(next_friday)})
            except BotBlocked:
                await asyncio.sleep(1)
            com_num += 1
            continue
        if len(com) % 2 == 0:
            j = 0
            while j < len(com):
                username_1 = await get_user_name(int(com[j]))
                username_2 = await get_user_name(int(com[j+1]))
                # username_1 = username_1.replace('_','\_')
                # username_2 = username_2.replace('_','\_')
                try:
#                    await bot.send_message(chat_id = int(com[j]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                    if username_2[0] == ' ':
                        await bot.send_message(chat_id = int(com[j]), text = "А вот и твой собеседник"+username_2+'\ntg://user?id='+str(int(com[j+1])))
                    else:
                        await bot.send_message(chat_id = int(com[j]), text = "А вот и твой собеседник @"+username_2+'\ntg://user?id='+str(int(com[j+1])))
                    await bot.send_message(chat_id = int(com[j]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
                    # print(username_2, "А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j+1]))+')')
                    # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j+1]))+')', parse_mode='MarkdownV2')
                except BotBlocked:
                    await asyncio.sleep(1)
                try:
#                    await bot.send_message(chat_id = int(com[j+1]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                    if username_1[0] == ' ':
                        await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник"+username_1+'\ntg://user?id='+str(int(com[j])))
                    else:
                        await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник @"+username_1+'\ntg://user?id='+str(int(com[j])))
                    # await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')', parse_mode='MarkdownV2')
                    await bot.send_message(chat_id = int(com[j+1]), text = "Договоритесь о времени и месте встречи. Крайний срок встречи - следующий четверг")
                    # print(username_1, "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')')
                    # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')', parse_mode='MarkdownV2')
                except BotBlocked:
                    await asyncio.sleep(1)
                await week_pairs_collection.insert_one({'user_id_1': str(com[j]), 'user_name_1' : username_1,'user_id_2': str(com[j+1]), 'user_name_2' : username_2, 'community': str(coms[com_num]), 'week': str(next_friday)})
                print(j, coms[com_num])
                j += 2
        else:
            j = 0
            while j < len(com) - 3:
                username_1 = await get_user_name(int(com[j]))
                username_2 = await get_user_name(int(com[j+1]))
                # username_1 = username_1.replace('_','\_')
                # username_2 = username_2.replace('_','\_')
                try:
#                    await bot.send_message(chat_id = int(com[j]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                    if username_2[0] == ' ':
                        await bot.send_message(chat_id = int(com[j]), text = "А вот и твой собеседник"+username_2+'\ntg://user?id='+str(int(com[j+1])))
                    else:
                        await bot.send_message(chat_id = int(com[j]), text = "А вот и твой собеседник @"+username_2+'\ntg://user?id='+str(int(com[j+1])))
                    # await bot.send_message(chat_id = int(com[j]), text = "А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j+1]))+')', parse_mode='MarkdownV2')
                    await bot.send_message(chat_id = int(com[j]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
                    # print(username_2, "suka А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j]))+')')
                    # await bot.send_message(chat_id = 463776237, text = "suka А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j+1]))+')', parse_mode='MarkdownV2')
                except BotBlocked:
                    await asyncio.sleep(1)
                try:
#                    await bot.send_message(chat_id = int(com[j+1]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                    if username_1[0] == ' ':
                        await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник"+username_1+'\ntg://user?id='+str(int(com[j])))
                    else:
                        await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник @"+username_1+'\ntg://user?id='+str(int(com[j])))
                    # await bot.send_message(chat_id = int(com[j+1]), text = "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')', parse_mode='MarkdownV2')
                    await bot.send_message(chat_id = int(com[j+1]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
                    # print(username_1, "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')')
                    # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')', parse_mode='MarkdownV2')
                except BotBlocked:
                    await asyncio.sleep(1)
                await week_pairs_collection.insert_one({'user_id_1': str(com[j]), 'user_name_1' : username_1,'user_id_2': str(com[j+1]), 'user_name_2' : username_2, 'community': str(coms[com_num]), 'week': str(next_friday)})
                print(j, coms[com_num])
                j += 2
            username_1 = await get_user_name(int(com[-3]))
            username_2 = await get_user_name(int(com[-2]))
            username_3 = await get_user_name(int(com[-1]))
            # username_1 = username_1.replace('_','\_')
            # username_2 = username_2.replace('_','\_')
            # username_3 = username_3.replace('_','\_')

            try:
#                await bot.send_message(chat_id = int(com[-3]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                await bot.send_message(chat_id = int(com[-3]), text = "Количество участников из твоего комьюнити оказалось нечетным")
                await bot.send_message(chat_id = int(com[-3]), text = "И тебе выпала возможность пообщаться сразу с двумя людьми")
                await bot.send_message(chat_id = int(com[-3]), text = "Организуйте встречу на троих или можешь встретиться с каждым по отдельности")
                if username_2[0] == ' ':
                    await bot.send_message(chat_id = int(com[-3]), text = "Первый собеседник"+username_2+'\ntg://user?id='+str(int(com[-2])))
                else:
                    await bot.send_message(chat_id = int(com[-3]), text = "Первый собеседник @"+username_2+'\ntg://user?id='+str(int(com[-2])))
                if username_3[0] == ' ':
                    await bot.send_message(chat_id = int(com[-3]), text = "Второй собеседник"+username_3+'\ntg://user?id='+str(int(com[-1])))
                else:
                    await bot.send_message(chat_id = int(com[-3]), text = "Второй собеседник @"+username_3+'\ntg://user?id='+str(int(com[-1])))
                await bot.send_message(chat_id = int(com[-3]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
                # print(username_1, "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[j]))+')')
                # print(username_2, "А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[j]))+')')
                # print(username_3, "А вот и твой собеседник ["+username_3+'](tg://user?id='+str(int(com[j]))+')')
                # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_1+'](tg://user?id='+str(int(com[-3]))+')', parse_mode='MarkdownV2')
                # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_2+'](tg://user?id='+str(int(com[-2]))+')', parse_mode='MarkdownV2')
                # await bot.send_message(chat_id = 463776237, text = "А вот и твой собеседник ["+username_3+'](tg://user?id='+str(int(com[-1]))+')', parse_mode='MarkdownV2')
            except BotBlocked:
                    await asyncio.sleep(1)

            try:
#                await bot.send_message(chat_id = int(com[-2]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                await bot.send_message(chat_id = int(com[-2]), text = "Количество участников из твоего комьюнити оказалось нечетным")
                await bot.send_message(chat_id = int(com[-2]), text = "И тебе выпала возможность пообщаться сразу с двумя людьми")
                await bot.send_message(chat_id = int(com[-2]), text = "Организуйте встречу на троих или можешь встретиться с каждым по отдельности")
                if username_1[0] == ' ':
                    await bot.send_message(chat_id = int(com[-2]), text = "Первый собеседник"+username_1+'\ntg://user?id='+str(int(com[-3])))
                else:
                    await bot.send_message(chat_id = int(com[-2]), text = "Первый собеседник @"+username_1+'\ntg://user?id='+str(int(com[-3])))
                if username_3[0] == ' ':
                    await bot.send_message(chat_id = int(com[-2]), text = "Второй собеседник"+username_3+'\ntg://user?id='+str(int(com[-1])))
                else:
                    await bot.send_message(chat_id = int(com[-2]), text = "Второй собеседник @"+username_3+'\ntg://user?id='+str(int(com[-1])))
                # await bot.send_message(chat_id = int(com[-2]), text = "Первый собеседник ["+username_1+'](tg://user?id='+str(int(com[-3]))+')', parse_mode='MarkdownV2')
                # await bot.send_message(chat_id = int(com[-2]), text = "Второй собеседник ["+username_3+'](tg://user?id='+str(int(com[-1]))+')', parse_mode='MarkdownV2')
                await bot.send_message(chat_id = int(com[-2]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
            except BotBlocked:
                await asyncio.sleep(1)
            
            try:
#                await bot.send_message(chat_id = int(com[-1]), text = "Я сломався, но теперь я работаю. Если я скидывал тебе пару, то это было неправильно")
                await bot.send_message(chat_id = int(com[-1]), text = "Количество участников из твоего комьюнити оказалось нечетным")
                await bot.send_message(chat_id = int(com[-1]), text = "И тебе выпала возможность пообщаться сразу с двумя людьми")
                await bot.send_message(chat_id = int(com[-1]), text = "Организуйте встречу на троих или можешь встретиться с каждым по отдельности")
                if username_1[0] == ' ':
                    await bot.send_message(chat_id = int(com[-1]), text = "Первый собеседник"+username_1+'\ntg://user?id='+str(int(com[-3])))
                else:
                    await bot.send_message(chat_id = int(com[-1]), text = "Первый собеседник @"+username_1+'\ntg://user?id='+str(int(com[-3])))
                if username_2[0] == ' ':
                    await bot.send_message(chat_id = int(com[-1]), text = "Второй собеседник"+username_2+'\ntg://user?id='+str(int(com[-2])))
                else:
                    await bot.send_message(chat_id = int(com[-1]), text = "Второй собеседник @"+username_2+'\ntg://user?id='+str(int(com[-2])))
                await bot.send_message(chat_id = int(com[-1]), text = "Договоритесь о времени и месте встречи Крайний срок встречи - следующий четверг")
            except BotBlocked:
                await asyncio.sleep(1)

            await week_pairs_collection.insert_one({'user_id_1': str(com[-3]), 'user_name_1' : username_1,'user_id_2': str(com[-2]), 'user_name_2' : username_2, 'user_id_3': str(com[-1]), 'user_name_3' : username_3, 'community': str(coms[com_num]), 'week': str(next_friday)})
        com_num += 1

#screate_week_pairstart
@dp.message_handler(commands=['create_week_pairs'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, 'ща нахимичим')
    await create_week_pairs()
    await bot.send_message(message.chat.id, 'нахимичено, чекай логи')

#start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    print('start', message.from_user.username if message.from_user.username is not None else message.from_user.id, datetime.now())
    user_name = await user_info(message.from_user)
    await add_start(message.from_user.id, user_name)
    await bot.send_message(message.chat.id, 'Привет! Я бот Random Coffee')
    await bot.send_message(message.chat.id, 'Если кратко, то с моей помощью ты сможешь знакомиться с новыми людьми каждую неделю')
    await bot.send_message(message.chat.id, 'Каждую пятницу я буду рандомно выбирать пары людей из одного комьюнити и эти пары должны встретиться и, например, попить вместе чай/кофе и поговорить')
    await bot.send_message(message.chat.id, 'Так ты сможешь обзавестись кучей полезных знакомств и прокачать свои soft skills')
    await bot.send_message(message.chat.id, 'Если ты готов поучаствовать на следующей неделе, то жми /reg_next_week, я предложу тебе варианты комьюнити')
    await bot.send_message(message.chat.id, 'Ну а если ты хочешь узнать обо мне подробней или увидеть все команды, жми \n/help')

inline_btn_1 = InlineKeyboardButton('ВШЭ, 6 общежитие', callback_data='btn1')
inline_btn_2 = InlineKeyboardButton('ВШЭ, 8 общежитие (Трилистник)', callback_data='btn2')
inline_btn_3 = InlineKeyboardButton('ВШЭ, Дубки', callback_data='btn3')
inline_btn_4 = InlineKeyboardButton('ВШЭ, Севастополь', callback_data='btn4')
inline_btn_5 = InlineKeyboardButton('Тинькофф, Водный', callback_data='btn5')
inline_btn_6 = InlineKeyboardButton('МГУ', callback_data='btn6')
inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2).add(inline_btn_3).add(inline_btn_4).add(inline_btn_5).add(inline_btn_6)

inline_btn_1_del = InlineKeyboardButton('ВШЭ, 6 общежитие', callback_data='del1')
inline_btn_2_del = InlineKeyboardButton('ВШЭ, 8 общежитие (Трилистник)', callback_data='del2')
inline_btn_3_del = InlineKeyboardButton('ВШЭ, Дубки', callback_data='del3')
inline_btn_4_del = InlineKeyboardButton('ВШЭ, Севастополь', callback_data='del4')
inline_btn_5_del = InlineKeyboardButton('Тинькофф, Водный', callback_data='del5')
inline_btn_6_del = InlineKeyboardButton('МГУ', callback_data='del6')
inline_kb1_del = InlineKeyboardMarkup().add(inline_btn_1_del).add(inline_btn_2_del).add(inline_btn_3_del).add(inline_btn_4_del).add(inline_btn_5_del).add(inline_btn_6_del)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn'))
async def process_callback_kb1btn1(callback_query: types.CallbackQuery):
    code = int(''.join(filter(lambda i: i.isdigit(), callback_query.data)))
    # now = datetime.now()
    # next_monday = (now - timedelta(days = now.weekday()) + timedelta(days=7)).date()
    today = datetime.now()
    next_friday = (today + timedelta( (4-today.weekday()) % 7 )).date()
    print('Нажата кнопка добавления', globals()['inline_btn_%s' % code].text, callback_query.from_user.username if callback_query.from_user.username is not None else callback_query.from_user.id, datetime.now())
    if next_friday == today.date() and today.hour > 14 and today.minute > 3:
        next_friday += timedelta(7)
    next_week = str(next_friday)
    status = await want_to_coffee(user_id=callback_query.from_user.id, user_name=await user_info(callback_query.from_user), community=globals()['inline_btn_%s' % code].text, week=next_week)
    if status == 'already':
        await bot.answer_callback_query(callback_query.id)
        # await bot.send_message(callback_query.from_user.id, 'Ты уже есть в списках участников на следющую неделю в комьюнити '+globals()['inline_btn_%s' % code].text)
        await bot.send_message(callback_query.from_user.id, 'Ты уже есть в списках участников на следющую неделю')
    else:
        await bot.answer_callback_query(callback_query.id)
        if today.weekday() == 4 and today.hour > 14 and today.minute > 3:
            await bot.send_message(callback_query.from_user.id, 'Супер, записал тебя в список участников в комьюнити '+globals()['inline_btn_%s' % code].text)
            await bot.send_message(callback_query.from_user.id, 'Пару пришлю в следущую пятницу, так как сегодня уже произошла рандомизация пар на неделю')
        else:
            await bot.send_message(callback_query.from_user.id, 'Супер, записал тебя в список участников на следющую неделю в комьюнити '+globals()['inline_btn_%s' % code].text)
            await bot.send_message(callback_query.from_user.id, 'В пятницу пришлю твоего собеседника')
    
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('del'))
async def process_callback_kb1btn1(callback_query: types.CallbackQuery):
    code = int(''.join(filter(lambda i: i.isdigit(), callback_query.data)))
    # now = datetime.now()
    # next_monday = (now - timedelta(days = now.weekday()) + timedelta(days=7)).date()
    today = datetime.now()
    next_friday = (today + timedelta( (4-today.weekday()) % 7 )).date()
    print('Нажата кнопка удаления', globals()['inline_btn_%s_del' % code].text, callback_query.from_user.username if callback_query.from_user.username is not None else callback_query.from_user.id, datetime.now())
    if next_friday == today.date() and today.hour > 14 and today.minute > 5:
        next_friday += timedelta(7)
    next_week = str(next_friday)
    status = await week_collection.count_documents({'user_id': {'$eq': str(callback_query.from_user.id)}, 'community': {'$eq': str(globals()['inline_btn_%s_del' % code].text)}, 'week': {'$eq': str(next_week)}})
    if status != 0:
        await week_collection.delete_one({'user_id': {'$eq': str(callback_query.from_user.id)}, 'community': {'$eq': str(globals()['inline_btn_%s_del' % code].text)}, 'week': {'$eq': str(next_week)}})
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Хорошо, убрал тебя из списка '+globals()['inline_btn_%s_del' % code].text)
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Не вижу тебя в списке участников на следующую неделю в комьюнити '+globals()['inline_btn_%s_del' % code].text)

#reg_next_week
@dp.message_handler(commands=['reg_next_week'])
async def start(message: types.Message):
    print('reg_next_week', message.from_user.username if message.from_user.username is not None else message.from_user.id, datetime.now())
    await message.reply("Оки, теперь выбери комьюнити, в котором тебе подобрать собеседника на следующую неделю", reply_markup=inline_kb1)

#cancel_next_week
@dp.message_handler(commands=['cancel_next_week'])
async def start(message: types.Message):
    print('cancel_next_week', message.from_user.username if message.from_user.username is not None else message.from_user.id, datetime.now())
    await message.reply("Выбери комьюнити, я уберу тебя из списка участников на следующую неделю", reply_markup=inline_kb1_del)

#delete_me
@dp.message_handler(commands=['delete_me'])
async def start(message: types.Message):
    print('delete_me', message.from_user.username if message.from_user.username is not None else message.from_user.id, datetime.now())
    await users_collection.delete_one({'user_id': {'$eq': str(message.from_user.id)}})
    status = await week_collection.count_documents({'user_id': {'$eq': str(message.from_user.id)}}) ### ТУТ НАДО ПРАВИТЬ ПРИ УЧАСТИИ В НЕСКОЛЬКИХ КОМЬЮНИТИ
    if status != 0:
        await week_collection.delete_one({'user_id': {'$eq': str(message.from_user.id)}})
    await bot.send_message(chat_id = int(message.from_user.id), text = "Хорошо, тебе не будут приходить напоминания")
    await bot.send_message(chat_id = int(message.from_user.id), text = "Когда захочешь поучаствовать, нажми /reg_next_week")

#help
@dp.message_handler(commands=['help'])
async def start(message: types.Message):
    print('help', message.from_user.username if message.from_user.username is not None else message.from_user.id)
    await bot.send_message(message.chat.id, 'Random Coffee - достаточно распространненая практика')
    await bot.send_message(message.chat.id, 'Это не дейтинг, так что тут не будет предпочтений по полу')
    await bot.send_message(message.chat.id, 'Основная цель - найти новых друзей, обзавестись полезными знакомствами')
    await bot.send_message(message.chat.id, 'Команды: \n/reg_next_week - принять участие на следующей неделе\n/cancel_next_week - отменить участие на следующую неделю \n/delete_me - удалить себя из пользователей и отключить напоминания')
    await bot.send_message(message.chat.id, 'Если хочешь дать обратную связь или добавить свое комьюнити, то пиши @powerpuffluv123')

#help
@dp.message_handler(commands=['boltalka'])
async def start(message: types.Message):
    await boltalka()

# Получение сообщений от юзера
@dp.message_handler(content_types=["text"])
async def handle_text(message: types.Message):
    print('Обратная связь от ', message.from_user.username if message.from_user.username is not None else message.from_user.id, datetime.now(), message.text)
    today = str(datetime.now())
    username = await user_info(message.from_user)
    today_n = datetime.now()
    next_friday = (today_n + timedelta( (4-today_n.weekday()) % 7 )).date()
    await freetext_collection.insert_one({'date': today, 'user_id': str(message.from_user.id), 'user_name': username, 'text' : message.text})
    await bot.send_message(message.chat.id, 'Спасибо, я записал')
    if await week_collection.count_documents({'user_id': {'$eq': str(message.chat.id)}, 'week': {'$eq': str(next_friday)}}) == 0:
        await bot.send_message(message.chat.id, 'Если хочешь поучаствовать на следующей неделе, жми /reg_next_week')

############# reminder ###########################
async def next_week_reg_reminder():
    users_list = []
    today = datetime.now()
    next_friday = (today + timedelta( (4-today.weekday()) % 7 )).date()
    async for docs in users_collection.find():
        if int(docs['user_id']) not in users_list and await week_collection.count_documents({'user_id': {'$eq': docs['user_id']}, 'week': str(next_friday)}) == 0:
            users_list.append(int(docs['user_id']))
    for user in users_list:
        try:
            await bot.send_message(chat_id = int(user), text = "Хей🖖 не забудь принять участие на следующей неделе")
            await bot.send_message(chat_id = int(user), text = "Для этого нажми на /reg_next_week")
        except BotBlocked:
            await asyncio.sleep(1)

async def how_was_reminder():
    users_list = []
    today = datetime.now()
    prev_friday = str((today + timedelta( (4-today.weekday()) % 7 ) - timedelta(days=7)).date())
    async for docs in week_collection.find({'week':prev_friday}):
        if int(docs['user_id']) not in users_list:
            users_list.append(int(docs['user_id']))
    for user in users_list:
        try:
            await bot.send_message(chat_id = int(user), text = "Привет! Как прошла встреча?")
            await bot.send_message(chat_id = int(user), text = "Любая обратная связь важна для меня")
        except BotBlocked:
            await asyncio.sleep(1)

async def boltalka():
    user_list = [463776237, 449869512]
    for user in user_list:
        try:
            await bot.send_message(chat_id = user, text = "Пока могу отправлять только те сообщения, которые в меня заложили искусственно")
            await bot.send_message(chat_id = user, text = "Может быть, в будущем я научусь разговаривать, как полноценный человек")
        except BotBlocked:
            await asyncio.sleep(1)

async def next_week_cancel_reminder():
    users_list = []
    today = datetime.now().date()
    async for docs in week_collection.find({'week':str(today)}):
        if int(docs['user_id']) not in users_list:
            users_list.append(int(docs['user_id']))
    for user in users_list:
        try:
            await bot.send_message(chat_id = int(user), text = "Приветик! Через 5 минут я скину тебе твоего собеседника на следующую неделю")
            await bot.send_message(chat_id = int(user), text = "Если твои планы поменялись и ты не хочешь участвовать, нажми \n/cancel_next_week")
        except BotBlocked:
            await asyncio.sleep(1)

async def scheduler():
    aioschedule.every().wednesday.at("14:00").do(next_week_reg_reminder)
    aioschedule.every().friday.at("14:00").do(next_week_cancel_reminder)
    aioschedule.every().friday.at("14:05").do(create_week_pairs)
    aioschedule.every().thursday.at("20:00").do(how_was_reminder)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(3)
############# reminder ###########################



async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)

# async def send_messange():
#     for user in [463776237]:
#         await bot.send_message(chat_id = int(user), text = "Хей🖖 не забудь выбрать свой ужин сегодня")
#     print("Отправка завершена!")


# aioschedule.every().day.at("14:33").do(send_messange)

# while 1==1:
#     schedule.run_pending()
#     time.sleep(1)

# executor.start_polling(dp)

# @dp.message_handler()
# async def choose_your_dinner():
#     for user in [463776237]:
#         await bot.send_message(chat_id = int(user), text = "Хей🖖 не забудь выбрать свой ужин сегодня")

# async def scheduler():
#     aioschedule.every().day.at("18:20").do(choose_your_dinner)
#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(1)
        
# async def on_startup(dp): 
#     asyncio.create_task(scheduler())


