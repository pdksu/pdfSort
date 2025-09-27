import sys
import os
import subprocess
import signal
from PIL import Image, ImageShow
from functools import wraps

MAXCHOICES = 5

def cursor_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'stdscr' not in kwargs and not sys.platform.startswith('win32'):
            stdscr = curses.initscr()
            return func(*args, **kwargs, stdscr=stdscr)
        else:
            return func(*args, **kwargs)
    return wrapper

# Platform-specific imports and functions
if sys.platform.startswith('win32'):
    import msvcrt

    def get_key(stdscr):
        """Read single keypress from Windows console."""
        return msvcrt.getch().decode('utf-8')

else:
    import curses

    def get_key(stdscr):
        """Read single keypress from UNIX console."""
        key = stdscr.getch()
        if key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            return '\n'
        else:
            return chr(key)


class BackgroundViewer(ImageShow.MacViewer):
    """Custom viewer that doesn't steal focus on macOS."""
    def __init__(self):
        super().__init__()
        self.current_process = None
    def get_command(self, file, **options):
        """Use the -g flag to prevent focus stealing."""
        return f"open -g -a Preview.app {file}"

    def show_file(self, path, **options):
        """Display given file and track the process."""
        self.current_process = subprocess.Popen(['open', '-g', '-a', 'Preview.app', path])
        return 1

    def close(self):
        """Close the Preview window."""
        if self.current_process:
            try:
                subprocess.run(['osascript', '-e', 'tell application "Preview" to quit'])
                self.current_process = None
            except subprocess.SubprocessError:
                pass

# Register the background viewer at module import time
if sys.platform.startswith('darwin'):
    viewer = BackgroundViewer()
    ImageShow.register(viewer, 0)

@cursor_wrapper
def display_choices(likely_student, page: Image.Image, students, interactive=True, last_choice = None, recursive=False, stdscr=None , kill_viewer=True):
        if likely_student.shape[0] == 1:
            return likely_student
        elif not interactive: # without an operator, stack all the unclear results in one place
            return "DEFAULT"
        if not recursive:
            page.show()
        try:
            # Extract relevant column names
            first_name_col = [col for col in students.columns if col.lower().startswith('first')][0]  # Assuming there's only one column that starts with 'First'
            last_name_col = [col for col in students.columns if col.lower().startswith('last')][0]  # Assuming there's only one column that starts with 'Last'
            page_index_col = [col for col in students.columns if col.lower().startswith('page')][0]  # Assuming there's only one column that starts with 'Last'
            id_col = [col for col in students.columns if col == 'ID' or col == 'StudentId'][0]  # Hard coded, maybe there's something simpler that doesn't overlap with pageId
            # Helper function to display choices
            def show_choices(possible_choices, alternative):
                if len(possible_choices) <= MAXCHOICES:
                  for index, (_, student) in enumerate(possible_choices.iterrows(), 1):
                    # Printing only specific fields
                    print(f"({index}) {student[first_name_col]} {student[last_name_col]} {student[page_index_col]}\r", flush=True)
                    if index > MAXCHOICES:
                        break
                  print(alternative+"\r", flush=True)
                else:
                    print(f"TOO MANY, {alternative}\r", flush=True)
            if likely_student.empty:
                likely_student = [last_choice] + students.copy() if last_choice is not None else students.copy()
            # Variable to store the current substring of the name being spelled
            current_string = ""
            # Initial display of all likely student choices
            print("SHOWING CHOICES\r", flush=True)
            show_choices(likely_student, "(a-z) to spell, - to start over, # to select, / to skip\r")
            # Collect user input until a valid choice is made
            print("Choice (Enter to keep the last choice, - to start over, a-z to spell, / to skip):\r", flush=True)
            while True:
                choice = get_key(stdscr)
                if choice.isalpha():
                    letter = choice
                    print(f"got {letter}, {ord(letter)}\r", flush=True)
                    # Handle special keys
                    if ord(letter) == 27:  # ESC
                        return "DEFAULT"
                    if letter == '-':  # Dash for reset
                        return display_choices(likely_student=None, page=page, students=students, interactive=True, last_choice=last_choice, recursive=True)
                    current_string += letter
                    print(f"current string = {current_string}\r", end='', flush=True)
                    # Filter students based on the current substring
                    matching_students = students[students[first_name_col].str.lower().str.startswith(current_string.lower(), na=False)]
    
                    if matching_students.empty:
                        current_string = current_string[:-1]  # Remove the last letter
                        print(f"No matches found. Try again from {current_string}\r", flush=True)
                        continue
                    if matching_students.shape[0] == 1: # only one choice
                        return matching_students.iloc[0:1]
                    if matching_students.shape[0] < 5:
                        return display_choices(matching_students, page=page, students=students, last_choice=last_choice, interactive=True, recursive=True)
                    print(f"Still {matching_students.shape[0]} matches. Keep typing to narrow list...\r", flush=True)
                    likely_student = matching_students  # Reset the likely_student DataFrame
                elif choice.isdigit() and 1 <= int(choice) <= likely_student.shape[0]:
                    # Return the chosen student
                    return likely_student.iloc[int(choice) - 1:int(choice)]
                elif choice == '-':
                    return display_choices(likely_student=likely_student, page=page, students=students, last_choice=last_choice, interactive=True, recursive=True)
                elif choice == '\n' or (not choice and last_choice is not None):
                    return last_choice
                elif choice == '/': # skip page
                    return 'SKIP'
                else:
                    print("Invalid choice. Please try again.\r", flush=True)
        finally:
            if kill_viewer and not recursive and sys.platform.startswith('darwin'):
                viewer.close()  # Close Preview when we're done

@cursor_wrapper
def get_string_input(prompt, stdscr=None):
    print(prompt, end='', flush=True)
    chars = []
    while True:
        ch = get_key(stdscr)
        if ch in ('\n', '\r'):
            break
        elif ch in ('\b', '\x7f'):
            if chars:
                chars.pop()
                print('\b \b', end='', flush=True)
        else:
            chars.append(ch)
            print(ch, end='', flush=True)
    print()
    return ''.join(chars)