from django.template.defaulttags import register
import datetime


@register.filter
def date_f(obj):
    if obj:
        return datetime.datetime.strptime(obj, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y в %H:%M:%S')
    else:
        return '&ndash;'


@register.filter
def nbash(obj):
    if obj:
        return obj
    else:
        return '&ndash;'


@register.filter
def event_translate(obj):
    if obj == 'NOTE':
        return 'Добавление заметки'
    elif obj == 'UNSUB':
        return 'Отписка клиента'
    elif obj == 'EDIT':
        return 'Редактирование клиента'
    elif obj == 'FIX_CALL':
        return 'Фиксация последнего звонка'
    elif obj == 'CHARG_REQ':
        return 'Полный возврат денежных средств'
    elif obj == 'SEPARATOR_CHARG_REQ':
        return 'Частичный возврат'
    elif obj == 'PRE_CHARG_REQ':
        return 'Запрос клиента на возврат'
    elif obj == 'FIX_TELEGRAM':
        return 'Фиксация обращения по Telegram'
    elif obj == 'FIX_EMAIL':
        return 'Фиксация обращения по почте'
    elif obj == 'DELETE_ACC':
        return 'Удаление аккаунта'
    else:
        return '&ndash;'


@register.filter
def contacts(obj):
    if obj == 'phone':
        return 'Звонок'
    elif obj == 'email':
        return 'Почта'
    else:
        return 'Telegram'


@register.filter
def card_edit(obj):
    if obj:
        return f'{obj.replace("xxxxx","*")}'
    else:
        return '&ndash;'


@register.filter
def bank_name(obj):
    if obj:
        return obj
    else:
        return '&ndash;'

