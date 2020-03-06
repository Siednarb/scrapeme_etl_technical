import json

def getConfigField(*configFieldNames):
    '''returns the value of a configuration field. For embedded configuration names,
    pass each field as a new argument (eg: to get config['scrape']['url template']
    use getConfigField('scrape','url template')'''

    with open('./config.json','r') as f:
        config = json.load(f)

    if len(configFieldNames)==1:
        return config[configFieldNames[0]]
    elif len(configFieldNames)==2:
        return config[configFieldNames[0]][configFieldNames[1]]
    else:
        raise Exception("Invalid number of configuration fields in getConfigField()")