import sys

# Platform-specific imports and functions
if sys.platform.startswith('win32'):
    import msvcrt

    def get_key():
        """Read single keypress from Windows console."""
        return msvcrt.getch().decode('utf-8')

else:
    import curses

    def get_key():
        """Read single keypress from UNIX console."""
        stdscr = curses.initscr()
        curses.cbreak()
        stdscr.keypad(1)
        stdscr.addstr(0, 10, "Press a key")
        stdscr.refresh()
        key = stdscr.getch()
        curses.endwin()
        return chr(key)

def display_choices(likely_student, page, students, interactive=True):
    if likely_student.shape[0] == 1:
        return likely_student
    elif not interactive: # without an operator, stack all the unclear results in one place
        return "DEFAULT"

    page.show()

    # Extract relevant column names
    first_name_col = [col for col in students.columns if col.startswith('First')][0]  # Assuming there's only one column that starts with 'First'
    last_name_col = [col for col in students.columns if col.startswith('Last')][0]  # Assuming there's only one column that starts with 'Last'
    page_index_col = [col for col in students.columns if col.startswith('page')][0]  # Assuming there's only one column that starts with 'Last'
    # Helper function to display choices
    def show_choices(possible_choices, alternative):
        for index, (_, student) in enumerate(possible_choices.iterrows(), 1):
            # Printing only specific fields
            print(f"({index}) {student[first_name_col]} {student[last_name_col]} {student[page_index_col]}")
        print(alternative)

    # Initial display of all likely student choices
    show_choices(likely_student, "(s) Spell")

    # Variable to store the current substring of the name being spelled
    current_string = ""

    first_name_col = [col for col in students.columns if col.startswith('First')][0]  # Assuming there's only one column that starts with 'First'

    # Collect user input until a valid choice is made
    while True:
        if likely_student.empty:
            choice = "s"
        else:
            choice = input("Enter your choice: ")

        if choice == 's':
            print("Start typing the name [ESC to exit]...")

            current_string = ""
            while True:
                # Get single key stroke
                letter = get_key()
                print(f"got {letter}, {ord(letter)}", flush=True)

                # Use ESC key as exit mechanism, ASCII value for ESC is 27
                if ord(letter) == 27:
                    return "DEFAULT"

                current_string += letter
                print(f"current string = {current_string}", end='', flush=True)

                # Filter students based on the current substring
                matching_students = students[students[first_name_col].str.lower().str.startswith(current_string.lower(), na=False)]

                if matching_students.empty:
                    print("No matches found. Try again.")
                    current_string = current_string[:-1]  # Remove the last letter
                    continue

                if matching_students.shape[0] < 5:
                    print("")
                    show_choices(matching_students, "")
                    break  # Breaks out of the inner while loop

                print(f"{matching_students.shape[0]} matches found. Keep typing...")

            likely_student = matching_students  # Reset the likely_student DataFrame
            continue  # This continues the outer loop

        if choice.isdigit() and 1 <= int(choice) <= likely_student.shape[0]:
            # Return the chosen student
            return likely_student.iloc[int(choice) - 1:int(choice)]

        print("Invalid choice. Please try again.")