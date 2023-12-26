
from roster import complete_scores, gen_roster, DEF_SCORE_FIELDS
from pathlib import Path
from pandas import DataFrame, read_csv, concat

CSV_PATH_DEFAULT = Path(Path().absolute().parent,'csv_out')

def merge_scores(score_files : list, 
                 roster : Path = Path(CSV_PATH_DEFAULT, 'students_from_classroom.csv'),
                 f_out : str = None,
                 score_fields : list = DEF_SCORE_FIELDS ):
    """
    Merge multiple score files into a single wide-format DataFrame.

    Parameters:
    score_files (list): List of file paths to the score files.
    roster (Path, optional): Path to the roster file. Defaults to 'students_from_classroom.csv'.
    f_out (str, optional): Path for the output CSV file. If None, no file is saved.
    score_fields (list, optional): List of score field names to be included in the merge.

    Returns:
    tuple: A tuple containing the merged DataFrame and the score index DataFrame.
    """
    r = gen_roster(roster)
    merged = DataFrame()
    score_index = DataFrame({"file":[], "suffix":[]})
    for i, sfile in enumerate(score_files):
        score_index = concat([score_index, DataFrame({"file":sfile, "suffix":i}, index=[i])])
        cur_grades = read_csv(sfile).drop_duplicates()
        cur_filled_grades = complete_scores(cur_grades, r)
        rename_dict = {k: f'{k}{str(i)}' for k in score_fields}
        cur_filled_grades = cur_filled_grades.rename(columns=rename_dict)
        if merged.empty:
            merged = cur_filled_grades.copy()
        else:
            merged = merged.merge(cur_filled_grades[['ID']+list(rename_dict.values())], how="left", on="ID")
        if f_out:
            merged.to_csv(f_out, index=False)
            score_index_file = Path(f_out).parent / (Path(f_out).stem + '_index.csv')
            score_index.to_csv(score_index_file, index=False)
    return merged, score_index

if __name__ == '__main__':
    files = ['conserve energy quiz not-prob.csv',
             'conserve energy quiz prob.csv',
             'conserve energy quiz q3.csv',
             'conserve energy quiz q4.csv', ]
    files = ['Conserve m and e quiz q3.csv', 
             'Conserve m and e quiz.csv', 
             'Conserve momentum and energy quiz q4.csv',
             "Conserve p and E quiz q1.csv"]
    files = [Path(CSV_PATH_DEFAULT, f) for f in files]
    merge_scores(files, f_out = Path(CSV_PATH_DEFAULT, 'testmerge.csv'))

