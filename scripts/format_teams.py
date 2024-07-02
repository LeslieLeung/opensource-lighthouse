import csv
from pypinyin import lazy_pinyin


def is_chinese(char):
    return '\u4e00' <= char <= '\u9fff'


def sort_key(row):
    company = row['company']
    name = row['name']

    # sort company in lexicographical order first
    company_key = company

    # if company is Chinese, sort by pinyin
    if any(is_chinese(char) for char in company):
        company_key = ''.join(lazy_pinyin(company))

    # sort name in lexicographical order
    name_key = name

    return (company_key, name_key)


def sort_csv(input_file, output_file):
    # load csv file
    with open(input_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    sorted_rows = sorted(rows, key=sort_key)

    # write sorted rows to output file
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'company'])
        writer.writeheader()
        writer.writerows(sorted_rows)


if __name__ == "__main__":
    input_file = 'data/teams.csv'
    output_file = 'data/teams_formatted.csv'
    sort_csv(input_file, output_file)
