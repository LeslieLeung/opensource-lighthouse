import csv
from pypinyin import lazy_pinyin


def is_chinese(char):
    """判断一个字符是否是中文"""
    return '\u4e00' <= char <= '\u9fff'


def sort_key(row):
    company = row['company']
    name = row['name']

    # 先按字典序排序公司名
    company_key = company

    # 如果公司名是中文，再用拼音排序
    if any(is_chinese(char) for char in company):
        company_key = ''.join(lazy_pinyin(company))

    # 名字直接用字典序排序
    name_key = name

    return (company_key, name_key)


def sort_csv(input_file, output_file):
    # 读取CSV文件
    with open(input_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    # 按照company和name排序
    sorted_rows = sorted(rows, key=sort_key)

    # 写入新的CSV文件
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'company'])
        writer.writeheader()
        writer.writerows(sorted_rows)


if __name__ == "__main__":
    input_file = 'data/teams.csv'   # 输入文件名
    output_file = 'data/teams_formatted.csv'  # 输出文件名
    sort_csv(input_file, output_file)
