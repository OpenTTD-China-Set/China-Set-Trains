import re, openpyxl

wb = openpyxl.load_workbook('docs/str.xlsx')
ws = wb.active

strs = []
for row in ws.iter_rows():
    row_key = []
    for cell in row:
        row_key.append(cell.value)
    strs.append(row_key)
    print(row_key)

with open("lang/english.lng", 'w', encoding='utf-8') as f:
    f.write("##grflangid 0x01"+"\n")
    for i in range(len(strs)):
        if strs[i][1] == None:
            f.write(strs[i][0]+"\n")
        else:
            f.write(strs[i][0]+"   :"+strs[i][1]+"\n")

with open("lang/simplified_chinese.lng", 'w', encoding='utf-8') as f:
    f.write("##grflangid 0x56"+"\n")
    for i in range(len(strs)):
        if strs[i][2] == None:
            if strs[i][1] == None:
                f.write(strs[i][0]+"\n")
            else:
                pass
        else:
            f.write(strs[i][0]+"   :"+strs[i][2]+"\n")
   
