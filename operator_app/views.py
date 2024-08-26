import json
import os
import shutil
from collections import defaultdict

import requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import re
import pandas as pd

from variables import PROD_DOMAIN

BANKS = {
    "SBERBANK OF RUSSIA": "Сбербанк",
    "SBERBANK of Russia": "Сбербанк",
    "Sberbank": "Сбербанк",
    "QIWI Bank (JSC)": "Qiwi",
    "QIWI Bank": "Qiwi",
    "RNCB": "РНСБ",
    "Bank Otkritie Financial Corporation": "Открытие",
    "TINKOFF BANK": "Тинькофф",
    "Alfa-Bank": "Альфа-Банк",
    "JOINT STOCK COMPANY 'ALFA-BANK'": "Альфа-Банк",
    "Raiffeisenbank": "Райффайзенбанк",
    "Belarusbank JSC": "Беларусбанк",
    "Post Bank": "Почта Банк",
    "VTB Bank PJSC": "ВТБ",
    "VTB": "ВТБ",
    "Public Joint-Stock Company The Ural Bank for Reconstruction & Development": "УБРР",
    "Joint Stock Company Alfa-Bank": "Альфа-Банк",
    "Promsvyazbank": "Промсвязьбанк",
    "SAVINGS BANK OF THE RUSSIAN FEDERATION (SBERBANK)": "Сбербанк"
}


domain = PROD_DOMAIN


def redirect_from_superadmin(request):

    if request.GET:
        id_partner = request.GET['partner']
        request_auth = requests.get(f'{domain}/api/v1/operator/operators/{id_partner}/')
        user = json.loads(request_auth.content)
        request.session['id'] = user.get('id')
        request.session['user'] = user.get('email')

    return redirect('general')


def login_view(request):
    if request.session.get('user'):
        return redirect('general')

    if request.method == 'POST':

        if request.POST.get('type') == 'check_auth':
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember = request.POST.get('remember_me')

            request_auth = requests.post(
                f'{domain}/api/v1/operator/operators/authorization/',
                data={"email": email, "password": password}
            )

            response_auth = json.loads(request_auth.content)

            if response_auth.get('id'):
                '''начало сессии для пользователя при удачной аутентификации с присвоением email'''
                if remember:
                    '''Если пользователь поствил галочку "Запомнить меня" выставляю время сессии на 45 дней'''
                    request.session.set_expiry(value=3888000)
                request.session["id"] = response_auth.get('id')
                request.session['user'] = email
            return HttpResponse(request_auth)

    data = {'title': 'Авторизация пользователя'}

    return render(request, 'login.html', data)


def history_view(request):
    if request.session.get('id') is None:
        return redirect('login')

    today = datetime.now().strftime('%d.%m.%Y')
    date_replace = re.compile(r'(\d+).(\d+).(\d+)\sв\s(\d+):(\d+):(\d+)')

    history_today = json.loads(
        requests.post(
            f'{domain}/api/v1/operator/actions/filter/',
            data={'manager_id': request.session["id"]}
        ).content
    )
    if request.method == 'POST':
        if request.POST.get('type') == 'table_line':
            data = {
                'manager_id': request.session["id"],
                'date_from': request.POST.get('date_start_post'),
                'date_to': request.POST.get('date_end_post') if request.POST.get('date_end_post') else request.POST.get('date_start_post'),
                'phone': request.POST.get('phone_post') if request.POST.get('phone_post') else '',
                'email': request.POST.get('email_post') if request.POST.get('email_post') else '',
                'card': request.POST.get('card_post') if request.POST.get('card_post') else '',
                'action': request.POST.get('action_post') if request.POST.get('action_post') else '',
                'description': request.POST.get('note_tags_post') if request.POST.get('note_tags_post') else ''
            }

            history_filter = json.loads(
                requests.post(
                    f'{domain}/api/v1/operator/actions/filter/',
                    data=data
                ).content
            )
            for i in history_filter:
                i['description'] = date_replace.sub('', i.get('description'))
                if i.get('description').startswith(' -'):
                    i['description'] = i.get('description')[2:]
            return JsonResponse({'res': history_filter})

    for i in history_today:
        i['description'] = date_replace.sub('', i.get('description'))
        if i.get('description').startswith(' -'):
            i['description'] = i.get('description')[2:]

    data = {'title': 'История действий', 'today': today, 'history_today': history_today}
    return render(request, 'profile_history.html', data)


def charges_view(request):
    if request.session.get('id') is None:
        return redirect('login')

    try:
        shutil.rmtree(os.path.abspath(f"media/{request.session.get('id')}"))
    except FileNotFoundError:
        pass

    today = datetime.now().strftime('%d.%m.%Y')

    if request.method == 'POST':

        if request.POST.get('type') == 'download_charges_back':
            def replace_date_format(date_string: str) -> str:
                datetime_format = datetime.strptime(date_string, "%d.%m.%Y")
                new_str_format = datetime_format.strftime("%Y-%m-%d")
                return new_str_format

            start = replace_date_format(request.POST.get('date_start_post'))
            end = replace_date_format(request.POST.get('date_end_post'))

            request_data = requests.post(
                f"{domain}/api/v1/operator/operators/get_chargebacks_output/",
                json={
                    'start': start,
                    'end': end
                }
            )
            charges: list = json.loads(request_data.content).get("main")
            data_cumulated = json.loads(request_data.content).get("cumulated")
            changeed_columns = defaultdict(list)

            for column in charges:
                changeed_columns['id партнера'].append(column.get('partner'))
                changeed_columns['платежная система'].append(column.get('ps'))
                changeed_columns['id в нашей базе'].append(column.get('id_system'))
                changeed_columns['id платежной системы'].append(column.get('id_ps'))
                changeed_columns['сайт'].append(column.get('offer'))
                changeed_columns['банк'].append(column.get('bank'))
                changeed_columns['номер карты'].append(column.get('card'))
                changeed_columns['дата'].append(datetime.strptime(column.get('date')[:-7], "%Y-%m-%dT%H:%M:%S"))
                changeed_columns['сумма'].append(column.get('sum'))
                changeed_columns['валюта'].append(column.get('currency'))

            df = pd.DataFrame(changeed_columns)
            df = df.set_index('id партнера')
            df2 = pd.DataFrame([data_cumulated])

            dir_path = f'{os.path.abspath("media")}/{request.session.get("id")}/'
            file_name = f'{start}_{end}.xlsx'
            file_path = f'{dir_path}{file_name}'

            os.mkdir(dir_path)

            with pd.ExcelWriter(file_path) as writer:
                df.to_excel(writer, sheet_name="Чарджбеки")
                df2.to_excel(writer, sheet_name="Группировка по партнерам")

            output = {
                'folder': str(request.session.get("id")),
                'name': file_name,
            }

            return HttpResponse(json.dumps(output))

    data = {'title': 'Запрос данных по Чарджбекам', 'today': today}
    return render(request, 'charges.html', data)


def main_search_view(request):
    if request.session.get('id') is None:
        return redirect('login')

    if request.method == 'POST':

        if request.POST.get('type') == 'table_line':

            try:
                date_el = request.POST.get('date_time_post').replace(' ', '')
                datetime.strptime(date_el, '%d.%m.%Y%H:%M')
                date_el = request.POST.get('date_time_post')
            except ValueError:
                date_el = ''

            sum_trans = request.POST.get('sum_trans_post').replace(' ', '').replace(',', '.')

            req_client_data = {
                'phone': request.POST.get('phone_post') if request.POST.get('phone_post') else '',
                'email': request.POST.get('email_post') if request.POST.get('email_post') else '',
                'card_num': request.POST.get('card_post') if request.POST.get('card_post') else '',
                'pay_date_time': date_el,
                'amount': sum_trans if date_el else '',
                'success_tr': request.POST.get('success_trans_post') if date_el else '',
                'transaction_id': int(request.POST.get('trans_id')) if request.POST.get('trans_id') else ''
            }

            if req_client_data:
                result_table = requests.post(
                    f'{domain}/api/v1/operator/clients/find/',
                    json=req_client_data
                )
                try:
                    result_table = json.loads(result_table.content)
                except:
                    result_table = ["Ошибка запроса, проверьте входные данные и попробуйте повторить"]
            else:
                result_table = []

            return JsonResponse({'res': result_table})

    help_information = 'Если конкретных данных нет, то следует сделать писк по дате и времени списания денежных средств, ' \
       'результатом будет список, клиентов, у которых было списание в данное времени +- 2 минуты'

    data = {
        'title': 'Страница поиска', 'help_information': help_information,
    }

    return render(request, 'search_page.html', data)


def client_page_view(request, client_id):
    if request.session.get('id') is None:
        return redirect('login')

    client_information = json.loads(
        requests.get(f'{domain}/api/v1/operator/clients/{client_id}/client/').content
    )

    offers = json.loads(
        requests.get(f'{domain}/api/v1/offers/').content
    ).get('results')
    offer_name = client_information[0].get('offer')
    offer = filter(lambda r: r.get('name') == offer_name, offers)

    try:
        client_action = (list(offer)[0]).get('user_stats_reports')
        client_action = client_action.replace('{id}', f'{client_id}')
        table = requests.get(client_action).text
    except:
        client_action = None
        table = None

    if client_information[0].get('phone'):
        phone = client_information[0].get('phone')
    else:
        phone = ''

    if request.method == 'POST':

        # вывод таблицы с активностью клиента
        if request.POST.get('type') == 'action_table_req':
            return JsonResponse({'table': table})

        # Запрос на полный возврат
        if request.POST.get('type') == 'req_chargeback':
            requests.patch(
                f'{domain}/api/v1/operator/clients/{client_id}/',
                data={"charge_date": datetime.now()}
            )

            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'CHARG_REQ',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})
        # Частичный возврат
        if request.POST.get('type') == 'separator_charge':
            amount = request.POST.get('transaction_sum')
            transaction_id = request.POST.get('transaction_id')
            requests.post(
                f'{domain}/api/v1/operator/clients/partition_refund/',
                data={"transaction_id": transaction_id}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'SEPARATOR_CHARG_REQ',
                    'description': f"{datetime.now().strftime('%d.%m.%Y в %H:%M:%S')} - Сумма возврата = {amount} р.",
                }
            )
            return JsonResponse({'status': 'ok'})
        # Запрос на фозврат зафиксирован
        if request.POST.get('type') == 'pre_req_chargeback':
            requests.patch(
                f'{domain}/api/v1/operator/clients/{client_id}/',
                data={"pre_payment_request": datetime.now()}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'PRE_CHARG_REQ',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})

        # Редактирование
        if request.POST.get('type') == 'edit_cl':
            req_client_data = {
                'phone': request.POST.get('phone_post'),
                'email': request.POST.get('email_post'),
                'password': request.POST.get('pwd_post')
            }
            req_client_data = {i: req_client_data[i] for i in req_client_data if req_client_data[i]}
            requests.post(
                f'{domain}/api/v1/operator/clients/{client_id}/edit/',
                data=req_client_data
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'EDIT',
                    'description': f"{datetime.now().strftime('%d.%m.%Y в %H:%M:%S')} - {req_client_data}",
                }
            )
            return JsonResponse({'status': 'ok'})
        # Отписка клиента
        if request.POST.get('type') == 'unsub_cl':
            requests.get(
                f'{domain}/api/v1/operator/clients/{client_id}/unsubscribe'
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'UNSUB',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})
        # Добавление заметки
        if request.POST.get('type') == 'note_cl':
            note_client = request.POST.get('note_post')
            requests.patch(
                f'{domain}/api/v1/operator/clients/{client_id}/',
                data={"note": note_client}
            )

            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'NOTE',
                    'description': f'{datetime.now().strftime("%d.%m.%Y в %H:%M:%S")} - {note_client}',
                }
            )
            return JsonResponse({'status': 'ok'})

        # Фикс звонка
        if request.POST.get('type') == 'fix_call':
            requests.post(
                f'{domain}/api/v1/operator/clients/set_contacts/',
                json={"client_id": client_id, "type": "phone"}
            )
            requests.patch(
                f'{domain}/api/v1/operator/clients/{client_id}/',
                data={"last_call": datetime.now()}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'FIX_CALL',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})
        # Фикс telegram
        if request.POST.get('type') == 'fix_telegram':
            requests.post(
                f'{domain}/api/v1/operator/clients/set_contacts/',
                json={"client_id": client_id, "type": "telegram"}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'FIX_TELEGRAM',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})
        # Фикс email
        if request.POST.get('type') == 'fix_email':
            requests.post(
                f'{domain}/api/v1/operator/clients/set_contacts/',
                json={"client_id": client_id, "type": "email"}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'FIX_EMAIL',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})

        # Удаление аккаунта
        if request.POST.get('type') == 'delete_client':
            requests.post(
                f'{domain}/api/v1/operator/clients/delete_profile/',
                json={'client_id': client_id}
            )
            requests.post(
                f'{domain}/api/v1/operator/actions/',
                data={
                    'manager_id': request.session['id'],
                    'client_id': client_id,
                    'email': client_information[0].get('email'),
                    'phone': client_information[0].get('phone'),
                    'card': client_information[0].get('card'),
                    'action': 'DELETE_ACC',
                    'description': datetime.now().strftime('%d.%m.%Y в %H:%M:%S'),
                }
            )
            return JsonResponse({'status': 'ok'})

    client_history_inf = json.loads(requests.post(
        f'{domain}/api/v1/operator/actions/filter/',
        data={'client_id': client_id, 'manager_id': request.session["id"]}).content
    )
    transactions_inf = json.loads(
        requests.get(f'{domain}/api/v1/operator/clients/{client_id}/transactions/').content
    )

    call_contacts = 0
    telegram_contacts = 0
    mail_contacts = 0
    try:
        contacts = json.loads(requests.post(
            f'{domain}/api/v1/operator/clients/get_contacts/',
            data={"client_id": client_id}
        ).content).get('contacts')

        for i in contacts:
            if i.get('type') == 'telegram':
                telegram_contacts += 1
            elif i.get('type') == 'phone':
                call_contacts += 1
            elif i.get('type') == 'email':
                mail_contacts += 1

        last_data = contacts[-1]
    except:
        contacts = ''
        last_data = ''

    for i in transactions_inf:
        if BANKS.get(i.get('issuer')):
            i['issuer'] = BANKS.get(i.get('issuer'))

    delete = False
    if client_information[0].get('email'):
        if client_information[0].get('email').find('___') > -1:
            delete = True
    elif client_information[0].get('phone'):
        if client_information[0].get('phone').find('___') > -1:
            delete = True

    help_information = 'Доступные данные и возможные действия по клиенту'
    data = {
        'title': 'Данные клиента', 'help_information': help_information, 'client_information': client_information[0],
        'transactions_inf': transactions_inf, 'id_client': client_id, 'client_history_inf': client_history_inf,
        'phone': phone, 'client_contacts': last_data, 'call_contacts': call_contacts, 'delete': delete, 'table': table,
        'mail_contacts': mail_contacts, 'telegram_contacts': telegram_contacts, 'client_action': client_action
    }

    return render(request, 'client_page.html', data)


def logout(request):
    request.session["id"] = None
    request.session["user"] = None
    return redirect('login')


def page_not_found(request, exception):
    return render(request, '404.html')


def handler500(request, exception=None):
    return render(request, '500.html', {})


def handler501(request, exception=None):
    return render(request, '501.html', {})