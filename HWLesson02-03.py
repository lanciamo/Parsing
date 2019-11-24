import re
import requests
import time

from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from requests.exceptions import HTTPError

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 ' \
             'Safari/537.36 '


def parse_hh(vacancy, pages, collection, mode="update"):
    search_url = "https://hh.ru/search/vacancy"

    for page in range(pages):

        time.sleep(1)

        params = {"text": f"{vacancy}", "page": f"{page}"}

        html = make_request(search_url, params=params)

        if html is None:
            continue

        soup = bs(html, 'lxml')
        job_list = soup.find_all("div", class_="vacancy-serp-item")
        for job in job_list:
            link = job.find('a').get('href', 'no link')
            span = job.find_all("span")
            name = span[0].text
            job_more = job.find_all('a')[1].text + ' ' + span[2].text + ' ' + span[5].text
            salary_div = job.find("div", class_="vacancy-serp-item__compensation")
            salary = "З/П не указана"
            if salary_div:
                salary = salary_div.get_text()

            if mode == "update":
                if not collection.find_one({"link": link}):
                    collection.insert_one(format_data(name, link, salary, job_more, "hh.ru"))
            else:
                collection.insert_one(format_data(name, link, salary, job_more, "hh.ru"))


def make_request(url, params):
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": f'{user_agent}'})
        resp.raise_for_status()
        return resp.text
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err} while parsing (maybe number of pages was too big)')


def format_data(name, link, salary, info, site):
    min_max = False
    if "—" in salary:
        min_s, max_s = salary.split("—")
        min_s = float("".join(re.findall(r"\d+", min_s)))
        min_max = True
    elif "-" in salary:
        min_s, max_s = salary.split("-")
        min_s = float("".join(re.findall(r"\d+", min_s)))
        min_max = True
    elif "от" in salary.lower():
        min_s = re.search(r"от\s*(\d+[^до]*)(до|руб|kzt|₽|USD)", salary.lower())
        min_s = float("".join(re.findall(r"\d+", min_s.group(1)))) if min_s else salary
        max_s = "-"
        min_max = True
    else:
        return {"name": name, "info": info, "link": link, "salary": salary, "site": site}
    if min_max:
        return {"name": name, "info": info, "link": link, "min_salary": min_s, "max_salary": max_s, "site": site}


def parse_superjob(vacancy, pages, collection, mode="update"):
    base_url = "https://www.superjob.ru"
    search_url = "https://www.superjob.ru/vacancy/search"

    for page in range(1, pages + 1):

        time.sleep(1)

        params = {"keywords": f"{vacancy}", "page": f"{page}", "geo[c][0]": "1"}

        html = make_request(search_url, params=params)

        if html is None:
            continue

        soup = bs(html, 'lxml')
        for job in soup.find_all("div", class_="f-test-vacancy-item"):
            links = job.find_all("a")
            vac_link = "No link"
            for link in links:
                if not (link.get("href", "No link").startswith("/clients")):
                    vac_link = link.get("href")
                    break

            job_html = make_request(base_url + vac_link, params={})
            job_soup = bs(job_html, 'lxml')
            job_info = job_soup.find("div", class_="_3MVeX")
            job_more = job_info.find("span", class_="_3mfro _1hP6a _2JVkc").getText()
            name = job_info.find("h1").get_text()
            salary = job_info.find("span", class_="_3mfro _2Wp8I ZON4b PlM3e _2JVkc").get_text()

            if mode == "update":
                if not collection.find_one({"link": base_url + vac_link}):
                    collection.insert_one(format_data(name, base_url + vac_link, salary, job_more, "superjob.ru"))
            else:
                collection.insert_one(format_data(name, base_url + vac_link, salary, job_more, "superjob.ru"))


def search_job(salary, collection):
    for job in collection.find({"min_salary": {"$gt": salary}}):
        print(
            "-" * 79 + f"\n{job['name']} ({job['link']})\nMin salary: {job['min_salary']}\nAdditional: {job['info']}\nMax salary: {job['max_salary']}\nSite: {job['site']}")


def main():
    action = input(
        "And what do you want?\n Choose:\n[1] Parsing everything all over again\n[2] Only update changes and "
        "additions\n "
        "[3] Show positions with a salary above a given \n[4] Drop current DataBase\n[5] Exit\n")

    client = MongoClient('localhost', 27017)
    db = client.jobs_database
    collection = db.jobs

    if action == "1":
        position = input("Input position your prefer: ")  # python
        page_num = int(input("For how many pages do you want go deeper : "))  # 2
        parse_hh(position, page_num, collection, mode="all")
        parse_superjob(position, page_num, collection, mode="all")
    elif action == "2":
        position = input("Input position your prefer: ")  # python
        page_num = int(input("For how many pages do you want go deeper : "))
        parse_hh(position, page_num, collection, mode="update")
        parse_superjob(position, page_num, collection, mode="update")
    elif action == "3":
        salary = float(input("From what salary will I look up?: "))
        search_job(salary, collection)
    elif action == "4":
        collection.drop()
    elif action == "5":
        return False


while __name__ == "__main__":
    if not main():
        break
