# search Genesis for Student Data with options (Student Default Age) export to
# to .xlsx then save as .csv put file name in SFILE
# the .xlsx also needs emails which should be merged from another Genesis sort!
#
# this code just does what I've needed to date. If a student list needs a different key
# in the future it will need additional bits added to it

SFILE <- "/Users/peterkaplan/Downloads/students_export.csv"
KEY <- NA

library(stringr)
library(tidyverse)
students <- read.csv(SFILE)
students$initials <- paste0(substr(students$First,1,1),substr(students$Last,1,1))
dob <- substr(students$DOB,1,2)
nstudents <- length(dob)
ninitials <- length(unique(students$initials))
if (ninitials == nstudents) {
  print("FI LI is unique for your student list")
  KEY <- "FILI"
} else {
  n_init_dob <- paste0(students$initials, dob) %>% unique %>% length
  if (n_init_dob == nstudents){
    print("FI LI Day of birth, is unique")
    KEY <- "FILIDOB"
  }
}

if (KEY == "FILI"){
  students$key <- dob
} else if (KEY == "FILIDOB")
{
  students$key <- paste0(students$initials,dob)
}
students$Student.Id <- str_pad(students$Student.Id, width = 5, pad = "0", side = "left")

write_csv(students[,c("Student.Id","Last","First","email","pageId")], "/Users/peterkaplan/Code/pdfSort/annual_setup/student_keys.csv")