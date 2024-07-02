import csv
from pypinyin import pinyin, lazy_pinyin


def sort_key(row):
    # 使用拼音进行排序，如果是中文字符
    company_key = ''.join(lazy_pinyin(row['company']))
    name_key = ''.join(lazy_pinyin(row['name']))
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
    output_file = 'data/teams.csv'  # 输出文件名
    sort_csv(input_file, output_file)
