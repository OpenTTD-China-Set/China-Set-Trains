import csv
import os

import sys

try:
    path = sys.argv[1]
except:
    print("Please input the path of the csv file.")

strs = []

with open(path, mode="r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        strs.append(row)

if not os.path.exists("lang/"):
    os.makedirs("lang/")

with open("lang/english.lng", "w", encoding="utf-8") as f:
    f.write("##grflangid 0x01" + "\n")
    for i in range(len(strs)):
        if strs[i][1] == "":
            f.write(strs[i][0] + "\n")
        else:
            f.write(f"{strs[i][0]:48} {':' + strs[i][1]:<10}\n")


def other_lang_generate(lang_name, lang_row, lang_code):
    with open("lang/" + lang_name + ".lng", "w", encoding="utf-8") as f:
        f.write("##grflangid " + lang_code + "\n")
        for i in range(len(strs)):
            if strs[i][lang_row] == "":
                if strs[i][1] == "":
                    f.write(strs[i][0] + "\n")
                else:
                    pass
            else:
                f.write(f"{strs[i][0]:48} {':' + strs[i][2]:<10}\n")


other_lang_generate("simplified_chinese", 2, "0x56")
