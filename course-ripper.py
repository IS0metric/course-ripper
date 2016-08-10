import requests
from lxml import html
import subprocess
import os
import re
from bs4 import BeautifulSoup


def get_coursepage(code):
    url = 'http://gla.ac.uk/coursecatalogue/course/?code=' + code
    print url
    coursepage = requests.get(url)
    return coursepage


def get_course_title_only(code):
    coursepage = get_coursepage(code)
    soup = BeautifulSoup(coursepage.content, 'lxml')
    title = [soup.find_all('h1')[2].string][0]
    return title


def latex_info(info):
    return '\\textbf{' + info['heading'] + '} ' + info['value'] + ' \\break\n'


def latex_subsection(section):
    string = '\\subsubsection*{' + section['heading'] + '}\n'
    string += section['value'] + '\n'
    return string


def latex_course(course):
    basic_info_list = [
        'session', 'school', 'credits', 'level', 'offered',
        'visiting_students', 'erasmus_students'
    ]
    generic_subsection_list = [
        'description', 'timetable', 'requirements_of_entry',
        'excluded_courses', 'co_requisites', 'assessment_weighting'
    ]
    string = '\\subsection{' + course["title"] + '}\n'
    for info in basic_info_list:
        string += latex_info(course[info])
    for subsection in generic_subsection_list:
        string += latex_subsection(course[subsection])

    string += '\\break \\textbf{' + course['assessment_date'][
        'heading'] + '}' + course['assessment_date']['value'] + '\n'
    string += latex_subsection(course['aims'])

    string += '\\subsubsection*{' + \
        course['learning_outcomes']['heading'] + '}\n'
    outcome_list = re.split(
        '\d+\. ', course['learning_outcomes']['value'])
    string += outcome_list[0] + '\n'
    string += '\\begin{enumerate}\n'
    for i in outcome_list[1:-1]:
        string += '\\item ' + i + '\n'
    string += '\\end{enumerate}\n'
    return string


def create_not_included_list(codes):
    string = '\\begin{itemize}\n'
    for code in codes:
        title = get_course_title_only(code)
        string += '\\item{' + title + '}\n'
    string += '\\end{itemize}\n'
    return string


def write_to_latex(codelist, unwanted_courses):
    abstract01 = "I created this document to practice parsing html and using\
        tools like Beautiful Soup which I've previously had little experience\
        in. As a result, it's not perfect.\\newline\
        It is also a slightly condensed all-in-one-place look at a selection\
        of courses that are available for fourth year computer science\
        students at the University of Glasgow. For the purposes of clarity I\
        have removed several courses from this selection. The following\
        courses have been omitted:"
    abstract02 = "For more insight into the project, to report issues or to\
        have a look at the code, have a look at the\
        \\href{https://github.com/IS0metric/course-ripper}{GitHub}."
    unincluded = create_not_included_list(unwanted_courses)
    with open('courses.tex', 'w') as f:
        f.write('\\documentclass{hitec}\n')
        f.write('\\usepackage[document]{ragged2e}\n')
        f.write('\\usepackage{hyperref}\n')
        f.write('\\usepackage{href}\n')
        f.write('\\setcounter{tocdepth}{4}\n')
        f.write('\\begin{document}\n')
        f.write('\\title{Fourth Year (2016-17) Courses}\n')
        f.write('\\author{Jack Parkinson}\n')
        f.write('\\date{August 2016}\n')
        f.write('\\maketitle\n')
        f.write('\\abstract{' + abstract01 + unincluded + abstract02 + '}\n')
        f.write('\\newpage\n\n')
        f.write('\\tableofcontents\n')
        f.write('\\newpage\n\n')
        all_courses = []
        sem1_courses = []
        sem2_courses = []
        for code in codelist:
            course = bsoup(get_coursepage(code))
            if course['offered']['value'] == 'Runs Throughout Semesters 1 and 2':
                all_courses.append(course)
            elif "1" in course['offered']['value']:
                sem1_courses.append(course)
            elif "2" in course['offered']['value']:
                sem2_courses.append(course)
        f.write('\\section{Semester 1 and 2 Courses}\n\n')
        for course in all_courses:
            try:
                f.write(latex_course(course))
            except UnicodeEncodeError as e:
                print e
                print 'Error in course: ' + course['title']
        f.write('\\section{Semester 1 Only Courses}\n\n')
        for course in sem1_courses:
            try:
                f.write(latex_course(course))
            except UnicodeEncodeError as e:
                print e
                print 'error in course: ' + course['title']
        f.write('\\section{Semester 2 Only Courses}\n\n')
        for course in sem2_courses:
            try:
                f.write(latex_course(course))
            except UnicodeEncodeError as e:
                print e
                print 'error in course: ' + course['title']
        f.write('\\end{document}')
    return None


def create_tex(unwanted_courses, wanted_courses=None):
    page = requests.get(
        'http://gla.ac.uk/coursecatalogue/courselist/?code=REG30200000&name=School+of+Computing+Science')
    tree = html.fromstring(page.content)
    spans = tree.xpath('//span/text()')
    codes = []
    if wanted_courses is None:
        for span in spans:
            if span[0:4] == "COMP" and span[7] == '4' and span not in unwanted_courses:
                codes.append(span)
    else:
        for span in wanted_courses:
            codes.append(span)
    write_to_latex(codes, unwanted_courses)
    return None


def main(unwanted_courses):
    create_tex(unwanted_courses)
    cmd = ['pdflatex', '-interaction', 'nonstopmode', 'courses.tex']
    proc = subprocess.Popen(cmd)
    proc.communicate()
    return None


def new_dict(heading, value):
    value = value.replace('%', '\%').replace('&', '\&').replace(u'\xa0', ' ')
    value = value.replace(u'\u25a0', '\\break').replace(u'\u037e', ';')
    return {
        'heading': heading,
        'value': value,
    }


def get_info_list(info_string, course):
    info_list = []
    split_on_newline = info_string.split("\n")
    for elem in split_on_newline:
        split = elem.split(": ")
        for s in split:
            info_list.append(s)
    info_list = info_list[1:-1]
    info_tags = [
        'session', 'school', 'credits', 'level', 'offered',
        'visiting_students', 'erasmus_students',
    ]
    i = 0
    for info_tag in info_tags:
        course[info_tag] = new_dict(
            info_list[i] + ': ', info_list[i + 1])
        i += 2
    return course


def bsoup(coursepage):
    soup = BeautifulSoup(coursepage.content, 'lxml')
    h1 = soup.find_all('h1')[2]
    html = h1.find_next_siblings()
    all_strings = [h1.string]
    for div in html:
        try:
            text = div.get_text()
        except:
            text = div.string
        if text is not None:
            all_strings.append(text)
    course = {'title': all_strings[0]}
    course = get_info_list(all_strings[1], course)
    course['description'] = new_dict(all_strings[2], all_strings[3])
    course['timetable'] = new_dict(all_strings[4], all_strings[5])
    course['requirements_of_entry'] = new_dict(all_strings[6], all_strings[7])
    course['excluded_courses'] = new_dict(all_strings[8], all_strings[9])
    course['co_requisites'] = new_dict(all_strings[10], all_strings[11])
    course['assessment_weighting'] = new_dict(all_strings[12], all_strings[13])
    course['aims'] = new_dict(all_strings[17], all_strings[18])
    date = all_strings[14].split(': ')
    course['assessment_date'] = new_dict(date[0] + ": ", date[1])
    course['learning_outcomes'] = new_dict(all_strings[19], all_strings[20])
    # TODO Doesn't parse Minimum Requirement for Award of Credit or
    # Reassessment Options
    return course

if __name__ == "__main__":
    unwanted_courses = [
        'COMPSCI4010', 'COMPSCI4009', 'COMPSCI4013', 'COMPSCI4024P',
        'COMPSCI4014', 'COMPSCI4012', 'COMPSCI4011', 'COMPSCI4038',
        'COMPSCI4015', 'COMPSCI4016', 'COMPSCI4046', 'COMPSCI4047',
        'COMPSCI4044', 'COMPSCI4070', 'COMPSCI4038',
    ]
    create_tex(unwanted_courses)
