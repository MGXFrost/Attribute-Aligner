from asyncio.windows_events import NULL
from cmath import nan
import PySimpleGUI as sg
import pyperclip
from html.parser import HTMLParser

a = 'dwwdwfgerfergerg'
#Отступ между атрибутами
additionalWhitspace = 1
#Приоритеты. Только один атрибут из группы может быть у элемента!
priorities = [
    ('cmptype'),
    ['name'],
    ['src'],
    ['srctype'],
    ['put', 'get'],
    ['len']
]

def getPriority(attr):
    for i, val in enumerate(priorities):
        if attr in val: 
            return i
    return -1

#TODO временный костыль. Переделать availableAttrs под вид priorities
def findMaxlen(arr, dict1):
    maxlen = 0
    for a in arr:
        if a in dict1:
            if dict1[a]['maxlen'] > maxlen:
                maxlen = dict1[a]['maxlen']
    return maxlen


class MyHTMLParser(HTMLParser):
    outStr = ''
    rows = []
    def handle_starttag(self, tag, attrs):
        entry = {'tag': tag, 'attrs': {}}
        self.outStr += 'Start tag:' + str(tag) + '\n'
        for attr in attrs:
            entry['attrs'][attr[0]] = attr[1]
            self.outStr += 'attr:' + str(attr) + '\n'
        self.rows.append(entry)
    def init_arrays(self):
        self.outStr = ''
        self.rows = []
        
layout = [
    [sg.Text("Input")],
    [sg.Multiline(size=(100, 15), key="Input", font='Consolas 12')],
    [sg.Button("Clear input")],
    [sg.Text("Output")],
    [sg.Multiline(size=(100, 15), key="Output", font='Consolas 12')],
    [sg.Button("Format"), sg.Button("Format from clipboard"), sg.Button("Copy output")]
]

# Create the window
window = sg.Window(title = "Attribute Sorter&Aligner V0.1", layout = layout)
parser = MyHTMLParser()

# Create an event loop
while True:
    event, values = window.read()

    if event == "Close" or event == sg.WIN_CLOSED:
        break
    elif event == "Clear input":
        window.Element('Input').update(value='')
    elif event == "Copy output":
        pyperclip.copy(values['Output'])
    elif event == 'Format' or event == 'Format from clipboard':
        inputStr = ''
        if event == 'Format from clipboard':
            inputStr = pyperclip.paste()
            window.Element('Input').update(value=inputStr)
        else:
            inputStr = str(values['Input'])
        #Парсим
        parser.init_arrays()
        parser.feed(inputStr)
        parser.close()
        #Создаем список всех атрибутов с порядком
        availableAttrs = {}
        maxTagLength = 0
        for el in parser.rows:
            #Максимальная ширина тэга
            if len(el['tag']) > maxTagLength:
                maxTagLength = len(el['tag'])
            #Атрибуты
            for attr in el['attrs']:
                if attr not in availableAttrs:
                    availableAttrs[attr] = {
                        'priority': getPriority(attr),
                        'maxlen': len(el['attrs'][attr])
                    }
                elif availableAttrs[attr]['maxlen'] < len(el['attrs'][attr]):
                    availableAttrs[attr]['maxlen'] = len(el['attrs'][attr])

        #Создаем новые строки
        result = ''
        for el in parser.rows:
            row = '<' + el['tag'] + ' ' * (maxTagLength - len(el['tag']) + additionalWhitspace)
            #Расставляем атрибуты с приоритетом
            for priority in priorities:
                attrAvailable = False
                hasAttr = False
                for attr in priority:
                    if attr in availableAttrs:
                        attrAvailable = True
                        aVal = el['attrs'].get(attr, NULL)
                        if aVal != NULL:
                            row += attr + '="' + aVal + '"' + ' ' * (availableAttrs[attr]['maxlen'] - len(aVal) + additionalWhitspace)
                            hasAttr = True
                            break
                if attrAvailable and not hasAttr:
                    row += ' ' * (len(attr) + findMaxlen(priority, availableAttrs) + 3 + additionalWhitspace)                      
            #Затем атрибуты без приоритета
            for attr in availableAttrs:
                if availableAttrs[attr]['priority'] == -1:
                    aVal = el['attrs'].get(attr, NULL)
                    if aVal != NULL:
                        row += attr + '="' + aVal + '"' + ' ' * (availableAttrs[attr]['maxlen'] - len(aVal) + additionalWhitspace)
                    else:
                        row += ' ' * (len(attr) + availableAttrs[attr]['maxlen'] + 3 + additionalWhitspace)
            #Закрываем строку
            result += row.rstrip() + '/>\n'
            
        window.Element('Output').update(value=result)
    #end while True

window.close()
