import logging
import re

import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler
import paramiko
import dotenv
import os
dotenv.load_dotenv()

#переменные для работы с ботом и ssh клиентом
TOKEN = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

DB_username=os.getenv('DB_USER')
DB_password=os.getenv('DB_PASSWORD')
DB_host=os.getenv('DB_HOST')
DB_port=os.getenv('DB_PORT')
DB_database=os.getenv('DB_DATABASE')
connection = None

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
        
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    update.message.reply_text('Сохранить найденные данные? Да/Нет')
    context.user_data['phoneNumberList']=phoneNumberList
    return 'writePhoneNumbers' # Завершаем работу обработчика диалога

def writePhoneNumbers(update: Update, context: CallbackContext):
    user_input=update.message.text
    if user_input.lower()=='да':
        phoneNumberList = context.user_data.get('phoneNumberList', [])
        if phoneNumberList:
            connection = None
            try:
                connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

                cursor = connection.cursor()
                for number in phoneNumberList:
                    cursor.execute("INSERT INTO phones (phnumber) VALUES (%s);", (number,))
                    connection.commit()
                logging.info("Команда успешно выполнена")
                update.message.reply_text('Сохранено')
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
                    return ConversationHandler.END
    else:
        update.message.reply_text('Не сохраняем')
        return ConversationHandler.END

def writeEmails(update: Update, context: CallbackContext):
    user_input=update.message.text
    if user_input.lower()=='да':
        emailList = context.user_data.get('emailList', [])
        if emailList:
            connection = None
            try:
                connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

                cursor = connection.cursor()
                for email in emailList:
                    cursor.execute("INSERT INTO emails (email) VALUES (%s);", (email,))
                    connection.commit()
                logging.info("Команда успешно выполнена")
                update.message.reply_text('Сохранено')
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
                    return ConversationHandler.END
    else:
        update.message.reply_text('Не сохраняем')
        return ConversationHandler.END

def validPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')
    return 'validPass'

def validPass(update: Update, context):
    user_input = update.message.text
    if (re.search('[A-Z]', user_input) and re.search('[a-z]', user_input) and re.search('[0-9]', user_input) and  re.search('[@#$%^&*()]', user_input)) and len(user_input) >= 8:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END

def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска почт: ')

    return 'findEmails'

def aptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета для отображения (all для всех):')

    return 'aptList'

def aptList(update: Update, context):
    user_input = update.message.text
    if user_input == 'all':
        packet='apt list'
    else:
        packet='apt list ' + user_input
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(packet + '|head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def findEmails (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'[\w\.-]+@[\w\.-]+(?:\.[\w]+)+')

    emailList = emailRegex.findall(user_input) 

    if not emailList:
        update.message.reply_text('Email адреса не найдены')
        return ConversationHandler.END
    
    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' 
        
    update.message.reply_text(emails) # Отправляем сообщение пользователю
    update.message.reply_text('Сохранить найденные данные? Да/Нет')
    context.user_data['emailList']=emailList
    return 'writeEmails'

#def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def free(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def ssfunc(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss | head -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def release(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('cat /etc/*-release')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def uname(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def uptime(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def df(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def mpstat(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def wfunc(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def auth(update: Update, context):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last -10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def critical(update: Update, context): # critical errors на rm_host

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -p 2 -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def psfunc(update: Update, context): # ps на rm_host

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def replLogs(update: Update, context): #Логи репликации с master
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('docker logs db 2>&1 | grep "replica" | tail -n20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def services(update: Update, context): #сервисы на rm_host

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service | head -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def getEmailsBD(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        emailRegex = re.compile(r'[\w\.-]+@[\w\.-]+(?:\.[\w]+)+')
        emailList = emailRegex.findall(str(data)) 
        emails = '' 
        for i in range(len(emailList)):
            emails += f'{i+1}. {emailList[i]}\n' 
        update.message.reply_text(emails)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def getPhonesBD(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phones;")
        data = cursor.fetchall()
        phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')
        phoneNumberList = phoneNumRegex.findall(str(data))
        phoneNumbers = ''
        for i in range(len(phoneNumberList)):
            phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        update.message.reply_text(phoneNumbers)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'writePhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, writePhoneNumbers)]
        },
        fallbacks=[]
    )

    convHandlerValidPass = ConversationHandler(
        entry_points=[CommandHandler('verify_password', validPassCommand)],
        states={
            'validPass': [MessageHandler(Filters.text & ~Filters.command, validPass)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'writeEmails': [MessageHandler(Filters.text & ~Filters.command, writeEmails)]
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptListCommand)],
        states={
            'aptList': [MessageHandler(Filters.text & ~Filters.command, aptList)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerValidPass)
    dp.add_handler(convHandlerGetAptList)
	
    dp.add_handler(CommandHandler("get_release", release))
    dp.add_handler(CommandHandler("get_uname", uname))
    dp.add_handler(CommandHandler("get_uptime", uptime))
    dp.add_handler(CommandHandler("get_df", df))
    dp.add_handler(CommandHandler("get_free", free))
    dp.add_handler(CommandHandler("get_mpstat", mpstat))
    dp.add_handler(CommandHandler("get_w", wfunc))
    dp.add_handler(CommandHandler("get_auth", auth))
    dp.add_handler(CommandHandler("get_critical", critical))
    dp.add_handler(CommandHandler("get_ps", psfunc))
    dp.add_handler(CommandHandler("get_ss", ssfunc))
    dp.add_handler(CommandHandler("get_services", services))

    dp.add_handler(CommandHandler("get_repl_logs", replLogs))
    dp.add_handler(CommandHandler("get_emails", getEmailsBD))
    dp.add_handler(CommandHandler("get_phones", getPhonesBD))
	# Регистрируем обработчик текстовых сообщений
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
