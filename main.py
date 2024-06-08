import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import gspread

df1 = pd.DataFrame()


def add_data_1(item):
    global df1
    temp_df1 = pd.DataFrame.from_dict(item, orient='index').T
    df1 = pd.concat([df1, temp_df1], ignore_index=True)
    df1 = df1.fillna("N/A")
    df1.infer_objects(copy=False)
    df1.to_excel('table_1.xlsx', index=False)


df2 = pd.DataFrame()


def add_data_2(item):
    global df2
    temp_df2 = pd.DataFrame.from_dict(item, orient='index').T
    df2 = pd.concat([df2, temp_df2], ignore_index=True)
    df2 = df2.fillna("N/A")
    df2.infer_objects(copy=False)
    df2.to_excel('table_2.xlsx', index=False)


def _get_name():
    res = requests.get("https://www.pro-football-reference.com/years/2023/draft.htm")
    soup = BeautifulSoup(res.text, 'lxml')
    name_block = soup.find(id='drafts').tbody.find_all('tr')
    players = {'info': []}
    for line in name_block:
        info_player = line.find_all('td')
        try:
            players['info'].append({'name': info_player[2].text, 'team': info_player[1].a.get('title')})
        except IndexError:
            continue
    with open('players.json', 'w') as file:
        json.dump(players, file, indent=4, ensure_ascii=False)


def get_info_cards():
    # status = input('Нужно ли обновить список игроков? Введите Y, если да, если нет то любое, кроме Y: ')
    # if status.capitalize() == 'Y':
    #     print('Обновление данных началось...')
    #     _get_name()
    with open('players.json', 'r') as file:
        names = json.load(file)

    for i, name in enumerate(names['info'], start=1):
        res = requests.get(f"https://www.sportscardspro.com/search-products?q=2023+panini+prizm+{name['name'].replace(' ', '+')}&type=prices")
        soup = BeautifulSoup(res.text, 'lxml')
        try:
            content = soup.find(id="games_table").tbody.find_all('tr')
        except AttributeError:
            continue
        table_2 = {}
        table_2['Name'] = name['name']
        table_2['Team'] = name['team']

        for j, card_content in enumerate(content, start=1):
            table_1 = {}
            colors = ['Green', 'Pink', 'Normal']
            try:
                set_card = card_content.find_all('td')[2].text
            except IndexError:
                continue
            if "2023 panini prizm" in set_card.lower():
                try:
                    title_card = card_content.find_all('td')[1].text.strip('\n ').replace('\n', " ")

                    try:
                        color_card = title_card.split('[')[1].split(']')[0]
                        if color_card == "RC":
                            color_card = "Normal"
                    except IndexError:
                        color_card = "Normal"
                except IndexError:
                    continue
                table_1['Name'] = name['name']
                table_1['Team'] = name['team']
                table_1['Title'] = title_card
                table_1['Sets'] = set_card
                table_1['Color'] = color_card
                # Новый код
                table_1['Ungraded'] = card_content.find_all('td')[3].span.text
                table_1['Grade 9'] = card_content.find_all('td')[4].span.text
                table_1['PSA 10'] = card_content.find_all('td')[5].span.text
                # Новый код
                add_data_1(table_1)
                if table_1['Color'] in colors:
                    if table_1['Color'] in table_2.keys():
                        pass
                    else:
                        table_2[table_1["Color"]] = table_1['Ungraded']

                print(j, title_card)
        add_data_2(table_2)
        print(f"Обработано имя {i} из {len(names['info'])}: {name['name']}")


def update_google_table(file_path, sheetname):
    df = pd.read_excel(file_path)
    df = df.astype(str)
    gc = gspread.service_account('key.jsonold')
    wks = gc.open("").worksheet(sheetname)
    wks.update([df.columns.values.tolist()] + df.values.tolist())


if __name__ == '__main__':
    get_info_cards()

    print('Сортируем данные...')
    df = pd.read_excel('table_1.xlsx')
    df = df.sort_values(by=['Sets', 'Title'])
    df.to_excel('table_1.xlsx', index=False)
    #
    # print('Сбор данных завершен')
    # update_google_table('table_1.xlsx', 'Лист1')
    # print('таблица 1 обновлена')
    # update_google_table('table_2.xlsx', 'Лист2')
    # print('таблица 2 обновлена')
    # print("Обновление данных завершено")
