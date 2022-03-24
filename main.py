from watchgod import Change, watch
from pathlib import Path
from ruamel.yaml import YAML
import os
import threading
import time
import re
import getopt
import sys

# converts a list to a string by blinly concatinating the elements
def listToString(list):
    ret = ''
    for element in list:
        ret += element
    return ret

# returns a dict in the form of { SUFFIX : CATEGORY }
def parseCategories(config):
    categories: dict = {}
    for category in config['Files']:
        for suffix in config['Files'][category]:
            categories.update({suffix:category})    
    return categories

# replaces all occurences of <X> with os.environ[X]
def replaceEnv(text):
    for bracedVar in re.findall(r"^\<.*>", text):
        var = bracedVar.removeprefix('<').removesuffix('>')
        text = text.replace(bracedVar, os.environ[var])
    return text

# watch a path for new files and move stuff around
def watchPath(dir, categories):
    for changes in watch(dir.as_posix()):
        for change in changes:
            if change[0] == Change.added:
                filepath = Path(change[1])
                suffix = listToString(filepath.suffixes).removeprefix('.')
                if filepath.is_file and suffix in categories:
                    destinationDir = dir.joinpath(Path(categories[suffix]))
                    destinationDir.mkdir(parents=True, exist_ok=True)
                    destination = destinationDir.joinpath(filepath.name)

                    # if a file already exists, append '_copy' to filename
                    if destination.exists():
                        destination = Path(destination.as_posix() + '_copy')
                    os.rename(filepath, destination)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:")
        yaml = YAML();
        config = yaml.load(open(opts[0][1], 'r').read())
    except:
        print("use -c <PATH> to specify path to config file")
        return
    
    categories = parseCategories(config)

    print('watching:')
    for dir in config['Paths']:
        dirPrepared = replaceEnv(dir)
        print(dirPrepared)
        threading.Thread(target=watchPath, args=(Path(dirPrepared), categories), daemon=True).start()

    # wait for Interrupt signal to finish
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        return
        

if __name__ == "__main__":
    main()
