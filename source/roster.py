#  roster.py
#       tools for handling missing papers
#  gen_roster() generate blank .csv roster with scoring columns from classroom list
#  complete_scores() fill in .csv score sheet with zeros for missing students
#  complete_save_grades() || save_grades() save a roster or grades to a .csv file
#

from pandas import concat, read_csv, DataFrame
from pathlib import Path
import sys

DEF_ROSTER_FIELDS =  ["First", "Last", "ID", "Section", "prefix"]
DEF_SCORE_FIELDS = ["Score", "SelfA"]
DEF_PATH = Path().absolute() # current working directory

def gen_roster(fname : str, fields : list = DEF_ROSTER_FIELDS, folder: Path = DEF_PATH,
           scores: list=DEF_SCORE_FIELDS, fill = 0):
    """ fname is required
        returns a dataframe suitable for saving
    """
    students = read_csv(Path(folder, fname))
    try:
        roster = students[fields].copy()
    except KeyError as k:
        raise KeyError(f"{fname} is Missing field {k}")
    for score in scores:
        roster[score] = fill
    return roster

def complete_scores(grades: DataFrame, roster: DataFrame, 
                     scores: list = DEF_SCORE_FIELDS, key: str = "ID", 
                     keys: list = DEF_ROSTER_FIELDS+DEF_SCORE_FIELDS, fill=0):
    """ 
        take a dataframe of grades and a roster and fill in missing grades with 'fill'
        returns a dataframe with fields in 'keys'
    """
    newgrades = DataFrame({k:[] for k in keys}) # empty data frame
    for score in scores:
        roster[score] = fill

    for student in roster.iterrows():
        student = student[1]
        try:
            sgrade = grades.loc[grades[key]==student[key]]
            if len(sgrade) == 0:
                print(f"Filling {student['First']} {student['Last']}")
                newgrades.loc[len(newgrades)] = {k:student[k] for k in keys}
            for score in scores:
                if not sgrade[score].all():
                    grades.loc[grades[key]==student[key], score] = fill
        except IndexError:
            newgrades = concat(newgrades, {k:student[k] for k in keys})
        except KeyError as ke:
            print(f"Key error \ngrades: {grades.columns}\nnewgrades {newgrades.columns} \nstudent{student.keys}\nerror{ke}")
    return concat([grades, newgrades])
    
def save_grades(grades: DataFrame, fout, folder: Path = DEF_PATH):
    grades.to_csv(Path(folder, fout), index=False)

def complete_save_grades(grades: DataFrame, fout, folder: Path = DEF_PATH, roster: str = 'students_from_classroom.csv'):
    r = gen_roster(roster, folder=folder)
    grades = read_csv(f_input).drop_duplicates()
    r = complete_scores(grades, r)
    save_grades(r, Path(folder, fout))
 

if __name__ == "__main__":
    f_roster = "students_from_classroom.csv" # in csv_out
    f_input, f_output = None, "roster_blank.csv"
    if len(sys.argv) >= 2:
        f_input = sys.argv[1]
    if len(sys.argv) >= 3:
        f_output = sys.argv[2]
    if len(sys.argv) == 4:
        f_roster = sys.argv[3]

    if f_input:
        grades = read_csv(f_input).drop_duplicates()
        complete_save_grades(grades, f_output, roster=f_roster, folder=Path(Path().absolute().parent,'csv_out'))
