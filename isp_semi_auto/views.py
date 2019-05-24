# https://www.w3schools.com/tags/ref_httpmethods.asp - GET VS POST

# Python builtins
import os
import ast
import re
from operator import itemgetter
from datetime import timedelta

# Python third-party libraries
from fuzzywuzzy import process
import pygsheets
from num2words import num2words

# Django modules
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.template import loader

# MyDjango
from .models import Student, Teacher, Gradebook, Assignment, StudentAssignmentGrades, \
    Subject, SubjectTemplate
from .forms import GradebookForm

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The ID and range of a sample spreadsheet.
# TODO allow specification of different spreadsheet ID
SPREADSHEET_ID = '1dtVhPNY4AcPt5f2wyk3VoKO3TTOB3GHZ4sGJKIxWyAU'


# TODO Seems out of place to run here
# pygsheets convenience functions
def sheet():
    cred_file_path = os.path.join(BASE_DIR, 'isp_semi_auto', 'cred.json')
    gc = pygsheets.authorize(service_file=cred_file_path)
    sht = gc.open_by_key(SPREADSHEET_ID)
    return sht


def populate_sheet_names(g_sheet):
    worksheet_list = g_sheet.worksheets()
    return worksheet_list


COHORT = {
    'J': 'JANUARY_EXTENDED',
    'F': 'FEBRUARY_STANDARD',
    'A': 'AUGUST_STANDARD',
    'M': 'May Express',
    'O': 'October Express'
}

SUBJECT = {
    'AE': 'Academic English',
    'IT': 'Information Technology'
}

# TODO Don't hard-code this. Generate by scraping site linked to gradebook
ELA_LINK = '<a href="https://ies.online-learning.net.au/course/view.php?id=28">ELA</a>'
IELTS_LINK = '<a href="https://ies.online-learning.net.au/course/view.php?id=47">IELTS</a>'

# Review of work completed constants:
ASSIGNMENTS_COMPLETED = 'You completed the following assignment: {}'
NO_ASSIGNMENTS_COMPLETED = 'You didn\'t complete any assignments'


# TODO move utility functions out of views
# TODO Check that i'm using the _ properly in function names
# Exceeds the criteria cutoff
def _ex_criteria_co(ele):
    # Returns the student we want dependent on exceeding a threshold
    return ele[0] if ele[1] > 88 else False


def _parse_name(name):
    if '( )' in name:
        print('It\'s formal time')
        p_name = name.replace(',', " ").replace('( )', "").rstrip()
    else:
        try:
            p_name = name.split(',')[1]
            p_name = p_name.split('(')[1]
            p_name = p_name.replace(')', "").rstrip()
        except IndexError:
            p_name = 'TYPE TEACHER NAME HERE AND SEE ADMINISTRATOR ABOUT HAVING YOUR NAME ADDED'
    return p_name


def _parse_completed_assignments(assignments):
    assignment_string = "<ul>"
    try:
        for k, v in assignments.items():
            assignment_string += f'<li>{k.strip()}: {int(v)} marks</li>'
        assignment_string += '</ul>'
    except AttributeError:
        assignment_string = ""
    return assignment_string.rstrip()


def _parse_assigned_assignments(assignments):
    assignment_string = ""
    assignment_flavour = {
        'Quiz': [],
        'Assignment': [],
        'Interactive Content': [],
    }
    for assignment in assignments:
        assignment_flavour[assignment.get_flavour_display()].append(assignment.title)

    for k, v in assignment_flavour.items():
        if len(v) == 0:
            pass
        else:
            if len(v) == 1:
                p = False
            else:
                p = True
            if k == 'Quiz':
                if p:
                    noun = 'Quizzes'
                else:
                    noun = 'Quiz'
            elif k == 'Assignment':
                if p:
                    noun = k + 's'
                else:
                    noun = k
            elif k == 'Interactive Content':
                noun = k
            # TODO CATCH THIS REFERENCE ERROR
            assignment_string += f'<strong>{noun}</strong><ul>'
            for item in v:
                assignment_string += f'<li><a href="">{item}</a></li>'
            assignment_string += '</ul><br>'
    return assignment_string


def _replace_substrings_in_string(rep_lookup, template):
    to_replace = dict((re.escape(k), v) for k, v in rep_lookup.items())
    pattern = re.compile("|".join(to_replace.keys()))

    # Convert to string so regex can perform magic on in
    isp_string = ''.join(line for line in template)

    # Replace placeholders according to 'to_replace lookup'
    text = pattern.sub(lambda m: to_replace[re.escape(m.group(0))], isp_string)
    # Need a to convert from string to list for tui-editor; split on \n

    tui_list = text.split('\n')
    stripped_tui_list = [line.rstrip('\n') for line in tui_list]
    return stripped_tui_list


def _has_template(subject, isp_flavour):
    try:
        file_name = ISP_TEMPLATE_LOOKUP[subject][isp_flavour]
        template_path = os.path.join(BASE_DIR, 'isp_semi_auto', 'templates', 'isp_templates', file_name)
        return True, template_path
    except KeyError:
        feedback = f'{SUBJECT[subject.upper()]} does not have an {isp_flavour} template\n'
        choices = 'Templates available:\n'
        rt = ISP_TEMPLATE_LOOKUP[subject].values()
        temp_available = [pt.split('_-_')[1].replace('-', ' ').replace('.txt', '') + '\n' for pt in rt]

        return False, feedback + choices + ''.join(temp_available)


def _generate_isp_from_template(student_name, teacher_name, template):
    s_name = student_name
    t_name = _parse_name(teacher_name)

    # Define what to replace
    to_replace = {
        "^^STUDENT_NAME^^": s_name,
        "^^TEACHER_NAME^^": t_name,
        "^^ELA_LINK^^": ELA_LINK,
        "^^IELTS_LINK^^": IELTS_LINK
    }

    return _replace_substrings_in_string(to_replace, template)


def _parse_attendance_fb(fb_list):
    ela_a_no = ela_a_date = ela_fb = ielts_a_no = ielts_a_date = ielts_fb = ""

    for (k, v) in fb_list:
        if 'ELA' in k:
            if k[-2:] == '_f':
                if len(v) == 0:
                    ela_fb = ''
                else:
                    ela_fb = f' Your ELA teacher gave you the following feedback: {v}'
            elif k[-2:] == '_l':
                if 'Name' in v:
                    ela_a_date = ""
                else:
                    ela_a_date = f'You most recently went to ELA in the week beginning {v}.'
            else:
                if int(v) == 0:
                    ela_a_no = f'You have not yet attended an ELA class. '
                elif int(v) == 1:
                    ela_a_no = f' In the week prior you attended just {num2words(int(v))} class. '
                else:
                    ela_a_no = f' In the week prior you attended {num2words(int(v))} classes. '

        else:
            if k[-2:] == '_f':
                if len(v) is 0:
                    ielts_fb = ''
                else:
                    ielts_fb = f' Your IELTS teacher gave you the following feedback: {v}'
            elif k[-2:] == '_l':
                if 'AE' in v:
                    ielts_a_date = ""
                else:
                    ielts_a_date = f'You most recently went to IELTS class in the week beginning {v}. '
            else:
                if int(v) == 0:
                    ielts_a_no = f'You have not yet attended an IELTS class. '
                elif int(v) == 1:
                    ielts_a_no = 'In the two weeks up to this date you attended just one IELTS class. '
                else:
                    ielts_a_no = f' In the two weeks up to this date you attended {num2words(int(v))} classes. '

    conglom_ela = ela_a_date + ela_a_no + ela_fb
    conglom_ielts = ielts_a_date + ielts_a_no + ielts_fb

    return conglom_ela, conglom_ielts


def _generate_followup_isp_from_template(student_name,
                                         teacher_name,
                                         feedback,
                                         assignments,
                                         completed_assignments,
                                         template_path):
    s_name = student_name
    t_name = _parse_name(teacher_name)

    # Gets a list to be consumed by the Select2 dropdown/text input
    if len(assignments) > 0:
        p_assignments = _parse_assigned_assignments(assignments)
    else:
        p_assignments = "Any tasks set by your teacher in AE or ELA class"
    # Completed assignments is a dict
    p_completed_assignments = _parse_completed_assignments(completed_assignments)
    # How many assignments were completed?
    if len(completed_assignments) == 0:
        what_student_did = NO_ASSIGNMENTS_COMPLETED

    # One completed item
    elif len(completed_assignments) == 1:
        what_student_did = ASSIGNMENTS_COMPLETED.format(p_completed_assignments)

    else:
        # It's not nothing - It's not 1, so construct correct pluralized language
        what_student_did = ASSIGNMENTS_COMPLETED. \
            replace('assignment', 'assignments'). \
            format(p_completed_assignments)

    feedback_list = sorted(list(feedback.items()), key=itemgetter(0))

    ela_fb, ielts_fb = _parse_attendance_fb(feedback_list)

    # Define what to replace
    to_replace = {
        "^^STUDENT_NAME^^": s_name,
        "^^TEACHER_NAME^^": t_name,
        "^^WHAT_STUDENT_DID^^": what_student_did,
        "^^ELA^^": ela_fb,
        "^^IELTS^^": ielts_fb,
        "^^WHAT_STUDENT_SHOULD_DO^^": p_assignments,
        "^^ELA_LINK^^": ELA_LINK,
        "^^IELTS_LINK^^": IELTS_LINK

    }
    return _replace_substrings_in_string(to_replace, template_path)


def _count_attendance(attendance_data_row, latest_col):
    attendance_count = 0
    teacher_note = ""
    for presence in attendance_data_row[latest_col - 1: latest_col]:
        # Target ps by themselves but not p's in names
        # split on 'p'
        # possible attendance p's
        is_p = presence.value.lower().split('p')

        # splitting on p gets a contiguous word back in a list of one if the cell being inspected is a name
        # test that the items returned by split are of 0 length
        # if the name contains a p will get a list on n+1 length where n is the number of p's in the name
        if max([len(i) for i in is_p]) in (0, 1):  # The length of the "," will be one
            attendance_count += (len(is_p) - 1)
            try:
                teacher_note += presence.note
            except TypeError:
                pass

    return attendance_count, teacher_note


def parse_attendance(gs, target_row):
    mra = target_row[-1].col  # Most recent attendance column
    mraw = gs.cell((1, int(mra))).value  # Most recent attendance week
    attendance_count, teacher_note = _count_attendance(target_row, mra)
    return attendance_count, teacher_note, mraw


def fill_out_isp(request):
    teacher = request.GET.get('teacher', '')
    subject = request.GET.get('subject', '')
    isp = request.GET.get('isp', '')
    step, flavour = isp.split('_')
    attendance = request.GET.get('attendance_choice_one', ''), request.GET.get('attendance_choice_two', '')

    fyid, student = request.GET.get('student', '').split('|')

    subject = Subject.objects.get(subject=subject)
    template = SubjectTemplate.objects.get(
        subject_name=subject, step=step, flavour=flavour)

    if '' in attendance:
        result = _generate_isp_from_template(student, teacher, template.template)  # FIXME
        return JsonResponse({
            'has_template': True,
            'template': result
        }, safe=False)

    else:
        fb = {}

        # The two choices back from the website
        for st in attendance:
            gsheet = GSHEET.worksheet_by_title(st)
            # Logic to account for inconsistent excel sheet formatting
            if 'IELTS' in st:
                target_names = gsheet.get_col(1, returnas='matrix', include_tailing_empty=False)
            else:
                # The names are in distinct columns
                # TODO this is redundant once application that populates gsheet template is in effect
                surname_list = gsheet.get_col(2, returnas='matrix', include_tailing_empty=False)
                name_list = gsheet.get_col(3, returnas='matrix', include_tailing_empty=False)
                target_names = [f'{x[0]}, {x[1]}' for x in zip(surname_list, name_list)]

            # Get the closest matching student, still might not be right, but don't worry
            # If the student can't be found because they don't exist, a gspread exception will catch that
            # If they can't be found because we're looking for a student that has their name split across two columns...
            # ... the IndexError will catch that

            # Returns false if not found care of _ex_criteria_co
            target_student = _ex_criteria_co(process.extractOne(student, target_names))

            if target_student:
                try:
                    # If it looks to be right should find a list with one cell in it, remove it from the list
                    cell = gsheet.find(target_student)[0]
                    # If the name is split across we'll get an index error,
                    target_row = gsheet.get_row(cell.row, returnas='cell', include_tailing_empty=False)
                    # Get the most recent attendance 'p or P'
                    fb[st], fb[st + '_f'], fb[st + '_l'] = parse_attendance(gsheet, target_row)

                    print(f'The students data has been found: {target_row}')

                except pygsheets.exceptions.CellNotFound:
                    print('A Cell not found exception has been thrown')
                    print(f'I\'m on the {st} iteration of the sheet inspection loop')
                    # The name might not be found because it is not in the sheet being inspected in this
                    # iteration of the for loop, perhaps because they haven't been populated to the list yet
                    # On because we're looking for it across two columns
                    fb += f' No student by the name {target_student} was found in the {st}'

                except IndexError:
                    print('An index error has been thrown')
                    print('Caused by slicing an empty list returned by gsheet.find??')
                    print(f'I\'m on the {st} iteration of the sheet inspection loop')
                    surname, given = target_student.split(',')  # Target student will never be a bool here pycharm
                    name_list = gsheet.get_col(3, returnas='cell', include_tailing_empty=False)

                    for cell in name_list:
                        if cell.value == given.strip():
                            target_row = gsheet.get_row(cell.row, returnas='cell', include_tailing_empty=False)
                            fb[st], fb[st + '_f'], fb[st + '_l'] = parse_attendance(gsheet, target_row)

                            print(f'The students data has been found: {target_row}')

            else:
                print('fuzzy search didn\'t find a match above the criteria')
                print(f'I\'m on the {st} iteration of the sheet inspection loop')
                fb[st] = 0

        # Get the latest gradebook and the gradebook closest to two weeks ago
        # If there is just the one gradebook, great! Use it to populate the assignment choices

        latest_gradebook = Gradebook.objects.filter(subject_choices=subject.subject).latest()
        past_gradebook = Gradebook.target.get_closest(target=(latest_gradebook.uploaded_at - timedelta(days=14)))

        # Can't evaluate an empty node, which would be the case if no homework was given
        try:
            tasks = ast.literal_eval(request.GET.get('tasks', ''))

        except SyntaxError:
            tasks = None

        if tasks is not None:
            a = [Assignment.objects.get(gradebook=latest_gradebook, js_id=i) for i in tasks]
            print(a)
        else:
            a = []
        s = Student.objects.get(fyid=fyid.strip())

        # Try to get the latest record of what the student has completed in the moodle gradebook
        try:
            latest_completed = StudentAssignmentGrades.objects.get(student=s, gradebook=latest_gradebook)
            past_completed = StudentAssignmentGrades.objects.get(student=s, gradebook=past_gradebook)
        except StudentAssignmentGrades.DoesNotExist:
            print('The student has not done anything and so there is no StudentAssignmentGrades saved for them')
            completed = 'Nothing'
        else:
            # What if there has just been the one gradebook uploaded thus far?
            if latest_completed.pk == past_completed.pk:
                completed = ast.literal_eval(latest_completed.grades)
                filter_out = ["-", None]
                completed = {k: v for k, v in completed.items() if v not in filter_out}
            else:
                latest_grades = ast.literal_eval(latest_completed.grades)
                past_grades = ast.literal_eval(past_completed.grades)
                completed = {k: latest_grades[k] for k in set(latest_grades) - set(past_grades)}
        fb_res = _generate_followup_isp_from_template(student,
                                                      teacher,
                                                      feedback=fb,
                                                      assignments=a,
                                                      completed_assignments=completed,
                                                      template_path=template.template,
                                                      )
        return JsonResponse({'has_template': True,
                             'template': fb_res}, safe=False)


def index(request):
    template = loader.get_template('isp_semi_auto/index.html')
    rendered_template = template.render({}, request)
    return HttpResponse(rendered_template, content_type='text/html')


@csrf_protect
def gradebook_upload(request):
    # POST to change
    if request.method == 'POST':
        form = GradebookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')

    else:
        form = GradebookForm()

    return render(request, 'isp_semi_auto/upload.html', {
        'form': form
    })


def subject_teachers(request):  # NOQA
    return JsonResponse([str(teacher) for teacher in Teacher.objects.all()], safe=False)


def subjects(request):
    # Get the teacher as part of the request
    # Teacher will inform the construction or not of an option menu
    # Triggered by the update of the teacher typeahead
    # Todo Teacher not in system?
    teacher = request.GET.get('teacher', '')

    lastname, firstnames = teacher.split(',')
    firstname, preferred = firstnames.split('(')

    teacher = Teacher.objects.filter(
        (Q(firstname__icontains=firstname.strip()) &
         Q(lastname__icontains=lastname.strip())) |
        Q(preferred__icontains=preferred.replace(')', '').strip())
    )

    subject_choice = [
        {'id': subject.subject,
         'display': str(subject)} for subject in teacher[0].subjects.all()]

    return JsonResponse(subject_choice, safe=False)


def isp_options(request):
    # Get the subject as part of the request
    # Teacher will inform the construction or not of an option menu
    # Triggered by the update of the teacher typeahead
    # Todo Teacher not in system?
    subject = request.GET.get('subject', '')
    subject = Subject.objects.get(subject=subject)
    isps = SubjectTemplate.objects.filter(subject_name=subject)

    isp_choices = [
        {'id': f'{isp.step}_{isp.flavour}',
         'display': isp.stage} for isp in isps]

    return JsonResponse(isp_choices, safe=False)


def attendance_options(request):
    global GSHEET
    GSHEET = sheet()

    cohorts = [cohort.title for cohort in populate_sheet_names(GSHEET)]
    ielts = set([x for x in cohorts if 'ELA' not in x])
    ela = set([x for x in cohorts if 'IELTS' not in x])

    inter = list(ielts.intersection(ela))
    both = list(ielts.union(ela))
    both.remove(inter[0])
    # A list of attendance choices perfect for a select2 like task assigning
    ielts = {"text": "IELTS",
             "children": []
             }

    ela = {"text": "ELA",
           "children": []
           }

    for i, att in enumerate(both):
        if att.find('IELTS') != -1:
            ielts['children'].append({'id': str(i), 'text': att})
        else:
            ela['children'].append({'id': str(i), 'text': att})

    return JsonResponse({"results": [ielts, ela]}, safe=False)


def assignments(request):
    chosen_subject = request.GET.get('subject', '')
    # If there have been no gradebook objects uploaded this will raise an DoesNotExist
    try:
        gradebook = Gradebook.objects.filter(subject_choices=chosen_subject).latest()
        assignments = Assignment.objects.filter(gradebook=gradebook)

        quiz = {"text": "Quiz",
                "children": []}
        assign = {"text": "Assignment",
                  "children": []}
        inter = {"text": "Interactive Content",
                 "children": []}

        for assignment in assignments:
            if assignment.flavour == 'Q':
                quiz["children"].append({"id": assignment.js_id,
                                         "text": assignment.title})
            elif assignment.flavour == "A":
                assign["children"].append({"id": assignment.js_id,
                                           "text": assignment.title})

            else:
                inter["children"].append({"id": assignment.js_id,
                                          "text": assignment.title})
    except Gradebook.DoesNotExist:
        pretty_subject = f'{SUBJECT[chosen_subject]}'
        return JsonResponse({
            # FIXME: Still looking for NO_GRADEBOOK or sumsuch in javascript
            "results": 'NO_GRADEBOOK',
            "subject": pretty_subject
        }, safe=False)

    return JsonResponse({"results": [quiz, assign, inter]}, safe=False)


def students(request):  # NOQA
    return JsonResponse([f'{s.fyid} | {str(s)}' for s in Student.objects.all()], safe=False)
