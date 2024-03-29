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
    ],
    # Изменение значения в атрибутах put/get: 0 - без изменений, 1 - заполнять пустые, 2 - форматировать все
    'putGetFill': 0,
    # Формат закрывающего тэга (для случая, когда контент элемент пуст): 0 - короткий />, 1 - полный ><elem/>
    'closingTagStyle': 0,
    # Не выравнивать атрибуты без приоритета (сортировка остается)
    'doNotAlignNonPriorityAttrs': False
}
# Имя файла кофигурации
filename = 'config.json'

######################## Code ########################
putGetFill_values = [
    'Do not change',
    'Fill empty using p|g+"name"',
    'Format ALL using p|g+"name"',
    'Remove get, empty put'
]
putGetFill_tooltip = '''Formats put/get attributes.
Do not change - leaves in the original version
Fill empty using p|g+name - fills empty attributes as follows: <component name="cmp1" put=""> -> <component name="cmp1" put="pCmp1">
Format ALL using p|g+name - similar to 'Fill empty', but also affects non-empty
Remove get, empty put - (current rules) removes get attribute and empties put according to the current regulation
'''
closingTagStyle_values = [
    'Short',
    'Full'
]

#Global variable definition
foundAttrs = {}
inputStr = ''
inputStrLower = ''

def hasPriorAttr(searchAttr):
    for prior in settings['priorities']:
        for attr in prior:
            if attr == searchAttr:
                return True
    return False

def getPriority(attr):
    for i, val in enumerate(settings['priorities']):
        if attr in val: 
            return i
    return -1

def getIntval(val, restirct="any"):
    try:
        v = int(val)
        if restirct == "pos":
            return abs(v)
        elif restirct == "neg":
            return -abs(v)
        else:
            return v
    except ValueError:
        return None

def updateSettingsIntval(settingName, windowElement, restirct="any"):
    a1 = getIntval(windowElement.get(), restirct)
    if a1 == None:
        windowElement.update(settings[settingName])
    else:
        settings[settingName] = a1
        windowElement.update(a1)

def getPriorities(window1):
    # Парсим приоритеты
    priorArr = []
    for r in window1.Element('attrPriorities').get().split('\n'):
        prior = []
        for a in r.split(','):
            a = a.strip()
            if ' ' not in a and len(a) > 0:
                prior += [a]
        if len(prior) > 0:
            priorArr += [prior]
    settings['priorities'] = priorArr

def getSettingsFromForm(window1):
    getPriorities(window1)
    putSettingsToForm(window1, 0)
    
    updateSettingsIntval('tagWhitespace', window1.Element('tagWhitespace'), "pos")
    
    updateSettingsIntval('additionalWhitespace', window1.Element('additionalWhitespace'), "pos")

    settings['removeBlankSpaceForLastAttr'] = window1.Element('removeBlankSpaceForLastAttr').get()

    settings['putGetFill'] = putGetFill_values.index(window1.Element('putGetFill').get())

    settings['closingTagStyle'] = closingTagStyle_values.index(window1.Element('closingTagStyle').get())

    settings['doNotAlignNonPriorityAttrs'] = window1.Element('doNotAlignNonPriorityAttrs').get()


def putSettingsToForm(window1, pos=-1):
    if pos == -1 or pos == 0:
        attrPriorities = ''
        for p in settings['priorities']:
            s = ''
            for a in p:
                s += a + ', '
            attrPriorities += s[:-2] + "\n"
        window1.Element('attrPriorities').update(attrPriorities)
    if pos == -1 or pos == 1:
        window1.Element('tagWhitespace').update(settings['tagWhitespace'])
    if pos == -1 or pos == 2:
        window1.Element('additionalWhitespace').update(settings['additionalWhitespace'])
    if pos == -1 or pos == 3:
        window1.Element('removeBlankSpaceForLastAttr').update(settings['removeBlankSpaceForLastAttr'])
    if pos == -1 or pos == 4:
        window1.Element('putGetFill').update(putGetFill_values[settings['putGetFill']])
    if pos == -1 or pos == 5:
        window1.Element('closingTagStyle').update(closingTagStyle_values[settings['closingTagStyle']])
    if pos == -1 or pos == 6:
        window1.Element('doNotAlignNonPriorityAttrs').update(settings['doNotAlignNonPriorityAttrs'])

def saveSettings(fname):
    configFile = open(fname, 'w')
    configFile.write(json.dumps(settings, indent="\t"))
    configFile.close()

def loadSettings(fname):
    rewriteConfig = False
    try:
        configFile = open(fname, 'r')
        readSettings = json.loads(configFile.read())
        configFile.close()
        for stgName in settings:
            if stgName in readSettings:
                settings[stgName] = readSettings[stgName]
            else:
                rewriteConfig = True  
    except (FileNotFoundError, json.JSONDecodeError):
        rewriteConfig = True
    
    # Убираем пустые значения из приоритетов
    new_priorities = []
    while len(settings['priorities']) > 0:
        priorInArr = settings['priorities'].pop()
        priorOutArr = []
        while len(priorInArr) > 0:
            prior = priorInArr.pop().strip()
            if ' ' not in prior and len(prior) > 0:
                priorOutArr = [prior] + priorOutArr
        if len(priorOutArr) > 0:
            new_priorities = [priorOutArr] + new_priorities
    settings['priorities'] = new_priorities

    #putGetFill
    if settings['putGetFill'] < 0 or settings['putGetFill'] > (len(putGetFill_values) - 1):
        settings['putGetFill'] = 0
        rewriteConfig = True

    if rewriteConfig:
        saveSettings(fname)

class MyHTMLParser(HTMLParser):
    rows = []
    def handle_starttag(self, tag, attrs):
        # Костыль для сохранения регистра букв
        ind = inputStrLower.find(tag)
        entry = {
            'tag': inputStr[ind:(ind + len(tag))], 
            'attrs': {},
            'content': ''
            }
        # Конец костыля
        
        for attr in attrs:
            entry['attrs'][attr[0]] = attr[1]

        #Автоисправление put/get атрибутов
        putVal = entry['attrs'].get('put', None)
        getVal = entry['attrs'].get('get', None)
        nameVal = entry['attrs'].get('name', None)
        if settings['putGetFill'] == 1 and nameVal != None and nameVal != '':
            if putVal != None and putVal == '':
                entry['attrs']['put'] = 'p' + nameVal[0].upper() + nameVal[1:]
            if getVal != None and getVal == '':
                entry['attrs']['get'] = 'g' + nameVal[0].upper() + nameVal[1:]
        elif settings['putGetFill'] == 2 and nameVal != None and nameVal != '':
            if putVal != None:
                entry['attrs']['put'] = 'p' + nameVal[0].upper() + nameVal[1:]
            if getVal != None:
                entry['attrs']['get'] = 'g' + nameVal[0].upper() + nameVal[1:]
        elif settings['putGetFill'] == 3:
            if putVal != None:
                entry['attrs']['put'] = ''
            if getVal != None:
                entry['attrs'].pop('get') 

        self.rows.append(entry)

    def handle_data(self, data):
        outdata = data.strip()
        #Присваиваем последнему элементу данные
        if len(self.rows) > 0 and len(outdata) > 0:
            self.rows[-1]['content'] = outdata

    def init_arrays(self):
        self.rows = []

# cat
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

# Create the window
col1 = [
    [sg.Text("Input")],
    [sg.Multiline(key="Input", font='Consolas 12', horizontal_scroll=True, expand_x=True, expand_y=True)],
    [sg.Button("Clear input")],
    [sg.Text("Output")],
    [sg.Multiline(key="Output", font='Consolas 12', horizontal_scroll=True, expand_x=True, expand_y=True)],
    [sg.Column([[sg.Button("Format"), sg.Button("Format from clipboard"), sg.Button("Copy output")]]), sg.Column([[sg.Button("Cat", key='Cat', visible=False)]], key='CatWrapper', expand_x=True)]
]
col2 = [
    [sg.Frame("(Debug) Found attributes", [
        [sg.Multiline(size=(25, 10), expand_x=True, key="availableAttrs", font='Consolas 12', disabled=True)],
        [sg.Button("Copy to priorities", key="copyFoundToPrior")]
    ])],
    [sg.Frame("Settings", [
        [sg.Text("Attribute priorities (sorting order)")],
        [sg.Multiline(size=(25, 10), expand_x=True, key="attrPriorities", font='Consolas 12')],
        [sg.Text("Format put/get attributes")],
        [sg.Combo(values=putGetFill_values, default_value=putGetFill_values[0], tooltip=putGetFill_tooltip, key="putGetFill", readonly=True)],
        [sg.Text("Closing tag style")],
        [sg.Combo(values=closingTagStyle_values, default_value=closingTagStyle_values[0], tooltip='Closing tag style', key="closingTagStyle", readonly=True)],
        [sg.Input(size=(5, None), key="additionalWhitespace"), sg.Text("Whitespace after tag")],
        [sg.Input(size=(5, None), key="tagWhitespace"), sg.Text("Whitespace between attributes")],
        [sg.Checkbox('Remove blank space for last attribute', key="removeBlankSpaceForLastAttr")],
        [sg.Checkbox('Do not align non-priority attributes', key="doNotAlignNonPriorityAttrs")],
        [sg.Button("Save settings"), sg.Button("Reload settings")]
    ])]
]

#expand_y
# ^
# |
# |----> expand_x
#size=(x, y)

layout = [
    [sg.Column(col1, expand_x=True, expand_y=True), sg.Column(col2, vertical_alignment="top")]
]

window = sg.Window(title = "Attribute Sorter&Aligner V0.3", layout = layout, finalize=True, resizable=True)
#Events
window['CatWrapper'].bind('<Enter>', '+mouseOver')
window['CatWrapper'].bind('<Leave>', '+mouseAway')

parser = MyHTMLParser()

# Load configuration
loadSettings(filename)
# Put settings to form
putSettingsToForm(window)

# Create an event loop
while True:
    event, values = window.read()

    if event == "Close" or event == sg.WIN_CLOSED:
        break
    elif event == 'Save settings':
        getSettingsFromForm(window)
        saveSettings(filename)
    elif event == 'Reload settings':
        loadSettings(filename)
        putSettingsToForm(window)
    elif event == "Clear input":
        window.Element('Input').update(value='')
    elif event == "Copy output":
        pyperclip.copy(values['Output'])
    elif event == "Cat":
        window.Element('Output').update(value=cat)
    elif event == "CatWrapper+mouseOver":
        window.Element('Cat').update(visible=True)
    elif event == "CatWrapper+mouseAway":
        window.Element('Cat').update(visible=False)
    elif event == "copyFoundToPrior":
        getPriorities(window)
        putSettingsToForm(window, 0)
        additionalAttrs = ''
        for key in foundAttrs:
            if not hasPriorAttr(key):
                additionalAttrs += '\n' + key
        if additionalAttrs != '':
            window.Element('attrPriorities').update(value=window.Element('attrPriorities').get() + additionalAttrs)
    elif event == 'Format' or event == 'Format from clipboard':
        #Получим настройки с формы
        getSettingsFromForm(window)

        inputStr = ''
        if event == 'Format from clipboard':
            inputStr = pyperclip.paste()
            window.Element('Input').update(value=inputStr)
        else:
            inputStr = str(values['Input'])

        inputStrLower = inputStr.lower()
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
        #foundAttrs не изменяется в алгоритме
        foundAttrs = availableAttrs.copy()
        # Отображаем атрибуты в окне
        avAttrStr = ''
        for a in foundAttrs:
            avAttrStr += a + "\n"
        window.Element('availableAttrs').update(value=avAttrStr)

        # Сортируем атрибуты
        outputOrder = []
        # Сортировка по приоритетам
        for priority in settings['priorities']:
            entry = {
                'attrs': [],
                'maxValLen': 0,
                'maxAttrLen': 0,
                'isPriority': True
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
                'maxAttrLen': len(maxAttr),
                'isPriority': False
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
                        # При включенной настройке атрибуты без приоритета не выравниваем
                        if settings['doNotAlignNonPriorityAttrs'] and not order['isPriority']:
                            rowAttr = attr + '="' + aVal + '"' + ' ' * settings['additionalWhitespace']
                        else:
                            rowAttr = attr + '="' + aVal + '"' + ' ' * (order['maxAttrLen'] - len(attr) + order['maxValLen'] - len(aVal) + settings['additionalWhitespace'])
                if rowAttr == None:
                    blankAttrSpace += order['maxAttrLen'] + order['maxValLen'] + 3 + settings['additionalWhitespace']
                else:
                    if settings['doNotAlignNonPriorityAttrs'] and not order['isPriority'] or settings['removeBlankSpaceForLastAttr'] and len(el['attrs']) == 0:
                        row += rowAttr
                    else:
                        row += ' ' * blankAttrSpace + rowAttr
                    blankAttrSpace = 0
            
            # Закрываем строку
            # Формат закрывающего тэга плюс контент
            closingTag = ''
            if len(el['content']) > 0:
                closingTag = '>' + el['content'] + '</' + el['tag'] + '>'
            elif settings['closingTagStyle'] == 1:
                closingTag = '></' + el['tag'] + '>'
            else:
                closingTag = '/>'
            
            result += row.rstrip() + closingTag + '\n'
            
        window.Element('Output').update(value=result)
    #end while True

window.close()