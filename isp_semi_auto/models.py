from django.db import models
from .csv_xlsx_utils import get_gradebook_items, get_student_items

COHORT = (
    ('J', 'Jan Extended'),
    ('F', 'Feb Standard'),
    ('A', 'Aug Standard'),
    ('M', 'May Express'),
    ('O', 'October Express'),
)

SUBJECT = (
    ('AE', 'Academic English'),
    ('IT', 'Information Technology'),
    ('BS', 'Behavioural Science'),
    ('MA', 'Mathematics'),
    ('CH', 'Chemistry'),
    ('PH', 'Physics'),
    ('AR', 'Architecture'),
    ('RE', 'Research'),
    ('AC', 'Accounting')
)

ASSIGNMENT_FLAVOUR = (
    ('Q', 'Quiz'),
    ('A', 'Assignment'),
    ('I', 'Interactive Content'),
)

STEPS = (
    ('1', 'Step 1.'),
    ('2', 'Step 2.'),
    ('3', 'Step 3.'),
    ('4', 'Step 4.'),
)

FLAVOURS = (
    ('a', 'A'),
    ('b', 'B'),
    ('c', 'C'),
    ('d', 'D'),
)


def unique_path(instance, filename):
    return '{}/{}'.format(instance.uploaded_at, filename)


class TargetGradebook(models.Manager):
    def get_closest(self, target):
        closest_greater_qs = self.filter(uploaded_at__gte=target).order_by('uploaded_at')
        closest_less_qs = self.filter(uploaded_at__lte=target).order_by('-uploaded_at')

        try:
            try:
                closest_greater = closest_greater_qs[0]
            except IndexError:
                return closest_less_qs[0]

            try:
                closest_less = closest_less_qs[0]
            except IndexError:
                return closest_greater_qs[0]
        except IndexError:
            raise self.model.DoesNotExist("There is no closest object"
                                          " because there are no objects.")

        if closest_greater.uploaded_at - target > target - closest_less.uploaded_at:
            return closest_less
        else:
            return closest_greater


class Gradebook(models.Model):
    cohort_choices = models.CharField(max_length=1, choices=COHORT)
    subject_choices = models.CharField(max_length=2, choices=SUBJECT)
    gb_xls = models.FileField(upload_to='gradebook/%Y-%m-%d/%H/%M')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()
    target = TargetGradebook()

    class Meta:
        get_latest_by = 'uploaded_at'

    def _update_assignments(self, created=False):
        if created:
            file = self.gb_xls.path

            cohort = self.cohort_choices
            assignments, fyids = get_gradebook_items(file)
            student_data, marks_lookup = get_student_items(file)

            assignments = [(i, assignment) for i, assignment in enumerate(assignments)]
            for (i, title) in assignments:
                if title[0:4] == 'Quiz':
                    p_title = title. \
                        replace('Quiz:', ''). \
                        replace('(Real)', ''). \
                        replace('Moodle', ''). \
                        replace('Quiz', ''). \
                        replace(' :', '')
                    flavour = 'Q'
                elif title[0:10] == "Assignment":
                    p_title = title. \
                        replace('Assignment:', ''). \
                        replace('(Real)', ''). \
                        replace('Moodle', ''). \
                        replace('Assignment', ''). \
                        replace('Portfolio:', ''). \
                        replace(' :', '')
                    flavour = 'A'
                else:
                    p_title = title. \
                        replace('Interactive Content:', ''). \
                        replace('(Real)', '')
                    flavour = 'I'

                # Update the assignments lest they have been added to since last gradebook upload
                Assignment.objects.get_or_create(
                    gradebook=self, js_id=str(i), flavour=flavour, title=p_title)

            # No students?
            for fyid, lastname, firstname, preferred in student_data:
                student = Student.objects.get_or_create(
                    fyid=fyid
                )[0]
                student.cohort_choices = cohort
                student.firstname = firstname
                student.lastname = lastname
                student.preferred = preferred
                student.save()
                # Get it if it exists
                student_assignment_grades = StudentAssignmentGrades.objects.get_or_create(
                    student=student, grades=marks_lookup[fyid]
                )

                if student_assignment_grades[1]:
                    # If creating a new set of assignment grades, because the original is not 'gotted'
                    # give the newly created gradebook to it so as it can be targeted later
                    student_assignment_grades[0].gradebook = self
                    student_assignment_grades[0].save()

    def save(self, *args, **kwargs):
        created = self.pk is None
        super(Gradebook, self).save(*args, **kwargs)
        self._update_assignments(created)

    def __str__(self):
        return f'{self.subject_choices} gradebook for' \
            f' {self.get_cohort_choices_display()} cohort, uploaded on {self.uploaded_at.strftime("%x")}'


class Assignment(models.Model):
    gradebook = models.ForeignKey(Gradebook, on_delete=models.CASCADE, null=True, blank=True)
    js_id = models.CharField(max_length=2)
    flavour = models.CharField(max_length=1, choices=ASSIGNMENT_FLAVOUR)
    title = models.CharField(max_length=130)

    def __str__(self):
        return self.title


class Cohort(models.Model):
    cohort_choices = models.CharField(max_length=1, choices=COHORT)


class Student(models.Model):
    fyid = models.CharField(max_length=8, null=True)
    cohort_choices = models.CharField(max_length=1, choices=COHORT)
    firstname = models.CharField(max_length=130)
    lastname = models.CharField(max_length=130)
    preferred = models.CharField(max_length=130, blank=True, null=True)

    def __str__(self):
        return f'{str(self.lastname).upper()}, {self.firstname} {self.preferred or ""}'

    def __repr__(self):
        return f'{str(self.lastname).upper()}, {self.firstname} {self.preferred or ""}'


class StudentAssignmentGrades(models.Model):
    student = models.ForeignKey(Student,
                                on_delete=models.CASCADE,
                                null=True, blank=True)
    gradebook = models.ForeignKey(Gradebook,
                                  on_delete=models.CASCADE,
                                  null=True, blank=True)
    grades = models.TextField(null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'uploaded_at'

    def __str__(self):
        return f'{str(self.student)}, {self.grades}'

    def __repr__(self):
        return f'{str(self.student)}, {self.grades}'

# ELI5 Many to many
# https://www.revsys.com/tidbits/tips-using-djangos-manytomanyfield/

# Many to many with custom through models
# https://gist.github.com/jacobian/827937


class Teacher(models.Model):
    firstname = models.CharField(max_length=130)
    lastname = models.CharField(max_length=130)
    preferred = models.CharField(max_length=130, blank=True, null=True)

    # With related name set, I can do: it.teachers.all() to get the it teachers
    subjects = models.ManyToManyField('Subject', related_name='teachers')

    def __str__(self):
        return f'{str(self.lastname).upper()}, {self.firstname} ({self.preferred or " "})'

    def __repr__(self):
        return f'{str(self.lastname).upper()}, {self.firstname} ({self.preferred or " "})'


class Subject(models.Model):
    subject = models.CharField(max_length=2, choices=SUBJECT, unique=True)

    def __str__(self):
        return self.get_subject_display()


def template_path(instance, filename):
    return f'isp_template/{str(instance.subject_name.subject)}/{instance.step+instance.flavour}/{filename}'


class SubjectTemplate(models.Model):
    # Fixme validation for if there is no pasted template nor uploaded template
    # Fixme population of Template text in TextField
    subject_name = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    step = models.CharField(max_length=1, choices=STEPS)
    flavour = models.CharField(max_length=1, choices=FLAVOURS)
    stage = models.CharField(max_length=45)
    template = models.TextField(help_text="Paste template here", null=True, blank=True) # Will be mandatory
    template_file = models.FileField(help_text="Upload template here", null=True, blank=True, upload_to=template_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'uploaded_at'

    def _populate_template_from_upload(self):

        try:
            with open(self.template_file.path) as f:
                print([line for line in f])
                isp_string = ''.join(line for line in f)
                self.template = isp_string
        except ValueError:
            pass

    """
    def __init__(self, *args, **kwargs):
        super(SubjectTemplate, self).__init__(*args, **kwargs)
        print('this is the template file')
        print(self.template_file)
        self.__template_file = self.template_file
        self._populate_template_from_upload()
        super(SubjectTemplate, self).save()
    """
    def save(self, *args, **kwargs):
        super(SubjectTemplate, self).save(*args, **kwargs)
        self._populate_template_from_upload()

    def __str__(self):
        return f'{self.stage} ISP template for' \
            f' {str(self.subject_name)} cohort, uploaded on {self.uploaded_at.strftime("%x")}'



