"""
This is used to generate the localization string

Uses en.json as the base file

Not to be ran externally
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import *

def get_keys(d: dict) -> List[str]:
    toRet = []
    for key, val in d.items():
        if isinstance(val, dict):
            inner_d = get_keys(val)
            for inner_k in inner_d:
                toRet.append(key + '.' + inner_k)
        else:
            toRet.append(key)
    return toRet

def main():
    p = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(p, 'en.json')) as f:
        dat = json.load(f)

    file_cont = []
    file_cont.append("\"\"\"")
    file_cont.append(f"Auto generated using {Path(__file__).name} on {datetime.now().isoformat()}")
    file_cont.append("\"\"\"")
    file_cont.append("from typing import Literal")
    file_cont.append("")
    file_cont.append("PrintTexts = Literal[")
    dot_keys = get_keys(dat)
    for key in dot_keys:
        file_cont.append(f"    \"{key}\",")
    file_cont.append("]")

    with open(os.path.join(p, 'define.py'), 'w') as f:
        f.write('\n'.join(file_cont))

if __name__ == '__main__':
    main()
else:
    raise UserWarning("Not supposed to import this file")