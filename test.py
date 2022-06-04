import json

filename = 'aaa.json'
#Отступ между атрибутами
additionalWhitespace = 1
#Отступ после тэга
tagWhitespace = 1
#Притягивать последний атрибут, если перед ним пустое место под предыдущий
removeBlankSpaceForLastAttr = False
#Приоритеты атрибутов. Атрибуты в одной группе (на одном уровне приоритета) взаимоисключающие!
priorities = [
    ['cmptype'],
    ['name'],
    #ActionVar
    ['src'],
    ['srctype'],
    ['put', 'get'],
    ['len'],
    #PopupItem
    ['caption'],
    ['onclick'],
    ['std_icon']
]
try:
    f = open(filename, 'r')
except FileNotFoundError:
    print('fileNotFound')
