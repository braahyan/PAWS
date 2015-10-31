import zipfile
import os


def zipdir(path, out_path):
    with zipfile.ZipFile(out_path, 'w') as ziph:
        for root, dirs, files in os.walk(path):
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(path):]  # XXX: relative path
                ziph.write(absfn, zfn)
    return out_path
