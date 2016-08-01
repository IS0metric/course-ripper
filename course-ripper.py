import requests
from lxml import html
import subprocess
import os
import re


def get_coursepage(code):
    url = 'http://gla.ac.uk/coursecatalogue/course/?code='+code
    print url
    coursepage = requests.get(url)
    return coursepage


def course_section(tree, heading, path='/following-sibling::div[1]/descendant::text()'):
    value = tree.xpath('//h4[text()="'+heading+'"]'+path)
    value = " ".join(value)
    section = {
        'heading': heading,
        'value': value.replace('%', '\%').replace('&', '\&').encode('utf-8')
    }
    return section


def parse_content(coursepage):
    tree = html.fromstring(coursepage.content)
    course = {}
    course['title'] = tree.xpath('//h1/text()')[1]
    course['assessment_date'] = {
        'heading': 'Main Assessment in: ',
        'value': tree.xpath('//h4[text()="Assessment"]/following::p/descendant::strong/parent::node()/text()')[0]
    }
    info_name = tree.xpath('//ul/descendant::strong/text()')
    info_data = tree.xpath('//ul[1]/descendant::*[not(self::strong)]/text()')
    info_tags = ['session', 'school', 'credits', 'level', 'offered', 'visiting_students', 'erasmus_students']
    for i in range(len(info_name)):
        course[info_tags[i]] = {
            'heading': info_name[i],
            'value': info_data[i + 25]
        }
    course['assessment_weighting'] = course_section(tree, 'Assessment')
    course['description'] = course_section(tree, 'Short Description')
    course['timetable'] = course_section(tree, 'Timetable')
    course['requirements_of_entry'] = course_section(tree, 'Requirements of Entry')
    course['excluded_courses'] = course_section(tree, 'Excluded Courses')
    course['aims'] = course_section(tree, 'Course Aims')
    course['learning_outcomes'] = course_section(tree, 'Intended Learning Outcomes of Course')
    course['co_requisites'] = course_section(tree, 'Co-requisites')
    return course


def latex_info(info):
    return '\\textbf{' + info['heading'] + '} ' + info['value'] + ' \\break\n'


def latex_subsection(section):
    string = '\\subsubsection*{' + section['heading'] + '}\n'
    string += section['value'] + '\n'
    return string


def latex_course(course):
    basic_info_list = ['session', 'school', 'credits', 'level', 'offered', 'visiting_students', 'erasmus_students']
    generic_subsection_list = ['description', 'timetable', 'requirements_of_entry', 'excluded_courses', 'co_requisites',
                               'assessment_weighting']
    string = '\\subsection{' + course["title"] + '}\n'
    for info in basic_info_list:
        string += latex_info(course[info])
    for subsection in generic_subsection_list:
        string += latex_subsection(subsection)

    string += '\\break \\textbf{'+course['assessment_date']['heading']+'}'+course['assessment_date']['value']+'\n'
    string += latex_subsection(course['aims'])

    string += '\\subsubsection*{' + course['learning_outcomes']['heading'] + '}\n'
    outcome_list = re.split('\d+\. ', course['learning_outcomes']['value'])
    string += outcome_list[0] + '\n'
    string += '\\begin{enumerate}\n'
    for i in outcome_list[1:-1]:
        string += '\\item ' + i + '\n'
    string += '\\end{enumerate}\n'
    return string


def create_latex(codelist):
    with open('courses.tex', 'w') as f:
        f.write('\\documentclass{hitec}\n')
        f.write('\\usepackage[document]{ragged2e}\n')
        f.write('\\setcounter{tocdepth}{2}\n')
        f.write('\\begin{document}\n')
        f.write('\\title{Fourth Year (2016-17) Courses}\n')
        f.write('\\author{Jack Parkinson}\n')
        f.write('\\date{August 2016}\n')
        f.write('\\maketitle\n')
        f.write('\\tableofcontents\n')
        all_courses = []
        sem1_courses = []
        sem2_courses = []
        for code in codelist:
            course = parse_content(get_coursepage(code))
            if "1" in course['offered']['value'] and "2" in course['offered']['value']:
                all_courses.append(course)
            elif "1" in course['offered']['value']:
                sem1_courses.append(course)
            elif "2" in course['offered']['value']:
                sem2_courses.append(course)
        f.write('\\section{Semester 1 and 2 Courses}\n')
        for course in all_courses:
            f.write(latex_course(course, f))
        f.write('\\section{Semester 1 Only Courses}\n')
        for course in sem1_courses:
            f.write(latex_course(course, f))
        f.write('\\section{Semester 2 Only Courses}\n')
        for course in sem2_courses:
            f.write(latex_course(course, f))
        f.write('\\end{document}')
    return None


def main():
    unwantedcourses = ['COMPSCI4010', 'COMPSCI4009', 'COMPSCI4013', 'COMPSCI4024P', 'COMPSCI4014', 'COMPSCI4012',
                       'COMPSCI4011', 'COMPSCI4038', 'COMPSCI4015', 'COMPSCI4016', 'COMPSCI4046', 'COMPSCI4047',
                       'COMPSCI4044', 'COMPSCI4070']
    page = requests.get('http://gla.ac.uk/coursecatalogue/courselist/?code=REG30200000&name=School+of+Computing+Science')
    tree = html.fromstring(page.content)
    spans = tree.xpath('//span/text()')
    codes = []
    for span in spans:
        if span[0:4] == "COMP" and span[7] == '4' and span not in unwantedcourses:
            codes.append(span)
    create_latex(codes)
    cmd = ['pdflatex', '-interaction', 'nonstopmode', 'courses.tex']
    proc = subprocess.Popen(cmd)
    proc.communicate()
    return None


if __name__ == "__main__":
    main()
