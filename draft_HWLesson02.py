from bs4 import BeautifulSoup as bs
import json
import requests
import pandas as pd

pd.options.display.max_rows = 200
pd.options.display.max_columns = 200
sj_link = 'https://www.superjob.ru'
hostSJ_geo = '%5Bc%5D%5B0%5D=1'  # На всю страну Russia
vacancies = []
name_of_vac = input('Название вакансии:')


def salary_eject(salary):
    if not salary or 'договорённости' in salary:
        return 0, 0
    salary = ''.join(salary.split())
    if 'от' in salary:
        salary = salary.replace('от', '').replace('₽', '')
        return int(salary), 0
    if 'до' in salary:
        salary = salary.replace('до', '').replace('₽', '')
        return 0, int(salary)
    if '—' in salary:
        salary = salary.replace('₽', '')
        salary = salary.split('—')
        return int(salary[0]), int(salary[1])
    return (0, 0)


def parse_sj(page_num):
    if page_num == 1:
        page1 = ''
    else:
        page1 = f'&page={page_num}'
    main_link = f'{sj_link}/vacancy/search/?keywords={name_of_vac}&geo{hostSJ_geo}{page1}'
    # print(main_link)
    try:
        req = requests.get(main_link).text
    except Exception:
        print(f'При подключении {main_link} возникла ошибка.')
    parsed_ht = bs(req, 'lxml')
    div_block = parsed_ht.find_all('div', {'class': '_3syPg _3P0J7 _9_FPy'})
    for div in div_block:
        try:
            vac_data = {}
            a_all = div.find_all('a')
            name_div = div.find('div', {'class': '_3mfro CuJz5 PlM3e _2JVkc _3LJqf'}).text
            sum_span = div.find('span', {'class': 'f-test-text-company-item-salary'}).text
            href_a = a_all[0]['href']
            href_link = sj_link + href_a
            comp = a_all[1].getText()
            time_div = div.find('span', {'class': '_3mfro _9fXTd _2JVkc _3e53o _3Ll36'})
            town_div = time_div.findNextSiblings()[0].text
            vac_data['site'] = 'superjob.ru'
            vac_data['position'] = name_div
            salary = salary_eject(sum_span)
            vac_data['salary_min'] = salary[0]
            vac_data['salary_max'] = salary[1]
            vac_data['salary'] = sum_span.replace('\xa0', ' ')
            vac_data['from'] = comp
            vac_data['city'] = town_div
            vac_data['time'] = time_div.getText()
            vac_data['link'] = href_link
            global vacancies
            vacancies.append(vac_data)
        except Exception as e:
            print(e)


for page in range(1, 6):
    parse_sj(page)

df = pd.DataFrame(vacancies)
print(df)
