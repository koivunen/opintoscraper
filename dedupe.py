
from constants import *
import code
from copy import deepcopy
import pathlib
from pathlib import Path
import logging
import hashlib



def dedupeSubfolders(path):
    global_hashes={}
    for folder in path.iterdir():
        if not folder.is_dir():
            continue
        #print("checking",folder)
        hashes=[]
        for file in folder.iterdir():
            if file.is_dir():
                continue
            #print("\t",file)
            sha1 = hashlib.sha1()
            with file.open("rb") as f:
                sha1.update(f.read())

            digest=sha1.digest()
            if digest in hashes:
                print("DEL",file)
                file.unlink()
            else:
                hashes.append(digest)

        for h in hashes:
            if global_hashes.get(h):
                print("crossdupe?",folder,global_hashes.get(h))
            else:
                global_hashes[h]=folder

if __name__ == '__main__':
    output_path = Path(OUTPUT_PATH)
    assert output_path.exists()
    dedupeSubfolders(output_path)