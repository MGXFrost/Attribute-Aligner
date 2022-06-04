import PySimpleGUI as sg
import pyperclip
import json
from html.parser import HTMLParser


######################## Default settings ########################
settings = {
    # Отступ между атрибутами
    'additionalWhitespace': 1,
    # Отступ после тэга
    'tagWhitespace': 1,
    # Притягивать последний атрибут, если перед ним пустое место под предыдущий
    'removeBlankSpaceForLastAttr': False,
    # Приоритеты атрибутов. Атрибуты в одной группе (на одном уровне приоритета) взаимоисключающие!
    'priorities': [
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
}
# Имя файла кофигурации
filename = 'config.json'

######################## Code ########################
def getPriority(attr):
    for i, val in enumerate(settings['priorities']):
        if attr in val: 
            return i
    return -1

class MyHTMLParser(HTMLParser):
    rows = []
    def handle_starttag(self, tag, attrs):
        entry = {'tag': tag, 'attrs': {}}
        for attr in attrs:
            entry['attrs'][attr[0]] = attr[1]
        self.rows.append(entry)
    def init_arrays(self):
        self.rows = []
        
layout = [
    [sg.Text("Input")],
    [sg.Multiline(size=(100, 15), key="Input", font='Consolas 12', horizontal_scroll=True)],
    [sg.Button("Clear input")],
    [sg.Text("Output")],
    [sg.Multiline(size=(100, 15), key="Output", font='Consolas 12', horizontal_scroll=True)],
    [sg.Button("Format"), sg.Button("Format from clipboard"), sg.Button("Copy output"), sg.Button("Cat")]
]

# Load configuration
rewriteConfig = False
try:
    configFile = open(filename, 'r')
    readSettings = json.loads(configFile.read())
    configFile.close()
    for stgName in settings:
        if stgName in readSettings:
            settings[stgName] = readSettings[stgName]
        else:
            rewriteConfig = True
        
except (FileNotFoundError, json.JSONDecodeError):
    rewriteConfig = True

if rewriteConfig:
        configFile = open(filename, 'w')
        configFile.write(json.dumps(settings, indent="\t"))
        configFile.close()

# Create the window
window = sg.Window(title = "Attribute Sorter&Aligner V0.2", layout = layout)
parser = MyHTMLParser()

cat = """
           ,     ,
           |\."./|
          / _   _ \\
         / (-) (-) \  _
         \==  Y  ==/ ( \\
          ;-._^_.-;   ) )
         /   \_/   \ / /
         |   (_)   |/ /
        /|  |   |  |\/
       | |  |   |  | |
        \|  |___|  |/
         '""'   '""'
"""

# Create an event loop
while True:
    event, values = window.read()

    if event == "Close" or event == sg.WIN_CLOSED:
        break
    elif event == "Clear input":
        window.Element('Input').update(value='')
    elif event == "Copy output":
        pyperclip.copy(values['Output'])
    elif event == "Cat":
        window.Element('Output').update(value=cat)
    elif event == 'Format' or event == 'Format from clipboard':
        inputStr = ''
        if event == 'Format from clipboard':
            inputStr = pyperclip.paste()
            window.Element('Input').update(value=inputStr)
        else:
            inputStr = str(values['Input'])
        # Парсим
        parser.init_arrays()
        parser.feed(inputStr)
        parser.close()
        # Создаем список всех атрибутов с порядком
        availableAttrs = {}
        maxTagLength = 0
        for el in parser.rows:
            # Максимальная ширина тэга
            if len(el['tag']) > maxTagLength:
                maxTagLength = len(el['tag'])
            # Атрибуты
            for attr in el['attrs']:
                if attr not in availableAttrs:
                    availableAttrs[attr] = {
                        'count': 1,
                        'maxValLen': len(el['attrs'][attr])
                    }
                else:
                    availableAttrs[attr]['count'] += 1
                    if availableAttrs[attr]['maxValLen'] < len(el['attrs'][attr]):
                        availableAttrs[attr]['maxValLen'] = len(el['attrs'][attr])
        
        # Сортируем атрибуты
        outputOrder = []
        # Сортировка по приоритетам
        for priority in settings['priorities']:
            entry = {
                'attrs': [],
                'maxValLen': 0,
                'maxAttrLen': 0
            }
            for attr in priority:
                if attr in availableAttrs:
                    entry['attrs'] += [attr]
                    if entry['maxValLen'] < availableAttrs[attr]['maxValLen']:
                        entry['maxValLen'] = availableAttrs[attr]['maxValLen']
                    if entry['maxAttrLen'] < len(attr):
                        entry['maxAttrLen'] = len(attr)
                    # Убираем атрибут
                    del availableAttrs[attr]
            if len(entry['attrs']) > 0:
                outputOrder += [entry]
        # Сортировка остального
        while len(availableAttrs) > 0:
            # Сортировка по количеству вхождений
            maxAttr = ''
            maxCount = 0
            
            for attr in availableAttrs:
                if maxCount < availableAttrs[attr]['count']:
                    maxCount = availableAttrs[attr]['count']
                    maxAttr = attr

            outputOrder += [{
                'attrs': [maxAttr],
                'maxValLen': availableAttrs[maxAttr]['maxValLen'],
                'maxAttrLen': len(maxAttr)
            }]

            del availableAttrs[maxAttr]

        # Создаем новые строки
        result = ''
        for el in parser.rows:
            row = '<' + el['tag'] + ' ' * (maxTagLength - len(el['tag']) + settings['tagWhitespace'])
            # Расставляем атрибуты
            blankAttrSpace = 0
            # Пробегаемся по приоритетам
            for order in outputOrder:
                rowAttr = None
                # Пробегаемся по атрибутам внутри приоритета
                for attr in order['attrs']:
                    aVal = el['attrs'].pop(attr, None)
                    if aVal != None and rowAttr == None:
                        rowAttr = attr + '="' + aVal + '"' + ' ' * (order['maxAttrLen'] - len(attr) + order['maxValLen'] - len(aVal) + settings['additionalWhitespace'])
                if rowAttr == None:
                    blankAttrSpace += order['maxAttrLen'] + order['maxValLen'] + 3 + settings['additionalWhitespace']
                else:
                    if settings['removeBlankSpaceForLastAttr'] and len(el['attrs']) == 0:
                        row += rowAttr
                    else:
                        row += ' ' * blankAttrSpace + rowAttr
                    blankAttrSpace = 0
            
            # Закрываем строку
            result += row.rstrip() + '/>\n'
            
        window.Element('Output').update(value=result)
    #end while True

window.close()