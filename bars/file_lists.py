# read file list from a .txt file with one line per row
# or from a .csv file with one line titled fname
#
import os
from pathlib import Path
import pandas as pd
from datetime import datetime as dt

# source directory
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

def list_from_file(fname, directory = ROOT_PATH, target_suffix=".pdf"):
    fname = Path(directory, fname)
    ftype = fname.suffix
    if ftype == ".txt":
        with open(fname) as f:
            listed = [l.strip().replace('\n','') for l in f.readlines()]
    elif ftype == ".csv":
        file_dframe = pd.read_csv(fname)
        fcol = [col for col in file_dframe if col.startswith('file')]
        if len(fcol) < 1:
            raise TypeError(f'file {fname} has no column starting with "file"')
        elif len(fcol) > 1:
            raise Warning(f'Multiple possible columns in {fname} using {fcol[0]}')
        fcol = fcol[0]
        dcol = [col for col in file_dframe if col.startswith('date')]
        if dcol:
            file_dframe.sort_values(dcol, inplace=True) # oldest first, most recent last
        listed = file_dframe[fcol].tolist()
    else:
        raise TypeError(f"file type {ftype} not implemented")
    listed = [l for l in listed if Path(directory, l).suffix == target_suffix]
    return listed

def files_to_list(dirname: Path, target_suffix: str=".pdf"):
    def fmtime(tstamp):
        return dt.fromtimestamp(tstamp).strftime("%Y-%m-%d %H:%M:%S")
    files = os.scandir(dirname)
    flist = pd.DataFrame({'file' : [f.name for f in files if Path(dirname,f).suffix == target_suffix]})
    flist['date'] = [fmtime(os.stat(Path(dirname, f)).st_birthtime) for f in flist['file']]
    return flist

def files_to_csv(dirname: Path, target_suffix: str=".pdf", outfile: str="scans.csv"):
    flist = files_to_list(dirname, target_suffix=target_suffix)
    flist.to_csv(Path(dirname, outfile), index=False)

if __name__ == "__main__":
    dpath = Path(ROOT_PATH,"..","pdf_out","scans")
    print(f"searching {dpath} which exits? {dpath.exists()}\n and has file {Path(dpath, 'scans.txt').exists()}")
    flist = list_from_file('scans.txt', directory = dpath)
    for f in flist:
        print(f)
    files_to_csv(dpath)
        
