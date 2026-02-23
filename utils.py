from phew import logging
import json

def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        logging.debug(f'Cannot read: {filename}')
        return { }

def save_json(filename, content):
    try:
        with open(filename, 'w') as f:
            json.dump(content, f)
            return True
    except:
        logging.debug(f'Cannot write {content} into {filename}')
        return False