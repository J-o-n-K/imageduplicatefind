import os
import sys

def main(root):
    print('Flattening', root)
    dirprune = []
    for directory, dirnames, filenames in os.walk(root):
        if root == directory:
            continue
        rootfiles = [f.lower() for f in os.listdir(root)]
        for filename in filenames:
            if filename.lower() in rootfiles: # make sure we check case insensitive
                print(directory,filename, 'already exists in',root)
            else:
                os.rename(os.path.join(directory,filename),os.path.join(root,filename))
                rootfiles.append(filename.lower()) # in case there were dupe cases from nix
        dirprune.append(directory)
    for rmd in reversed(dirprune):
        if os.path.exists(rmd):
            l = os.listdir(rmd)
            if len(l)==0:
                try:
                    os.removedirs(directory)
                except OSError as err:
                    print(err)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Need path to flatten')
        print('dirtreeflatten.py /some/directory/tree/to/flatten')
    else:
        main(sys.argv[1])

