// CSS
//https://medium.freecodecamp.org/css-naming-conventions-that-will-save-you-hours-of-debugging-35cea737d849

// JS
//http://snowdream.github.io/javascript-style-guide/javascript-style-guide/en/naming-conventions.html

$(function(){

    // Cache jQuery lookups
    var $teacher = $('#js-get-teachers');
    var $ispOptions = $('input[name="js-isp-options"]');
    var $subjectOptions = $('input[name="js-subject-options"]')
    var $student = $('#js-get-students');
    var $indicatorIsp = $('#js-indicator-isp');


    // Convenience functions
    function containsSubString(target, choices){
        // for each choice in choices of attendance
        var selected
        $.each(choices, function(index, choice){
            if (target.includes(choice)){
                selected = choice
            }
        })
        return selected
    };


    function refreshIsp(){
        editor.setValue('');
        //$attendanceData[0].selectedIndex = -1;
        $ispOptions.prop('checked', false);
        $homeworkAssigned.val(null).trigger('change');
        $attendanceInput.hide();
        $homeworkInput.hide();
    };


    function refreshRadios(){
        $('#js-isps').hide()
        $('#js-isp-options').empty()
        $('#js-subjects').hide()
        $('#js-subject-options').empty()
    }


    function renderAttendance(subject, flavour){
        console.log(subject)
        $('#js-attendance-options').select2({
            theme: "bootstrap",
            placeholder: 'ELA|IELTS' ,
            allowClear: true,
            ajax: {
                url: $('#js-attendance').attr('js-get-attendance-options-url'),
                async: true,
                type: "GET",
                dataType: 'json',
                data: {
                    'subject': subject,
                    'flavour': flavour
                    },
                success: function(result){

                    return result

                },
                error : function(xhr,errmsg,err) {
                    // Show an error
                    console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
                }
            }
        }).change(function(){

            // get the latest subject and flavour
            //var subject = $('#js-subject-options').attr('js-one-subject')
            // One subject has a length of 2,
            console.log(subject)
            if (subject.length != 2){
                subject = $('input[name="js-subject-options"]:checked').val()
            }
            var flavour = $('input[name="js-isp-options"]:checked').val()
            // Is it English? Is it a followup? if so check that one each of ELA and IELTS has been selected
            if (subject == 'AE'){

                // Render the attendance choices
                if( $(this).val().length == 2 ){
                    var selections = $(this).select2('data')
                    var choiceOne = selections[0].text
                    var choiceTwo = selections[1].text
                    var choices = ['ELA', 'IELTS'];
                    var attendOne = containsSubString(choiceOne, choices);
                    var attendTwo = containsSubString(choiceTwo, choices);

                    if (attendOne != attendTwo){

                        // Allow input into the student name
                        $student.prop('disabled', false);
                    } else {

                        alert('Choose one each of ELA Attendance and IELTS Attendance')
                        $(this).val(null).trigger('change')
                        $student.prop('disabled', true);
                    }
                } else if ($(this).val().length > 2) {
                    // Fixme clear selections in select2
                    $(this).val(null).trigger('change')
                    alert('Choose ONE each of ELA Attendance and IELTS Attendance')
                    $student.prop('disabled', true);
                } else {
                    console.log('What else could possibly happen?')
                }

            } else if (subject != 'AE') {
                if( $(this).val().length == 1 ){

                // Subjects that are not AE aren't going to assign IELTS
                // Make sure that the selection isn't ielts
                    var selection = $(this).select2('data')[0].text
                    if (selection.includes('IELTS')){
                        $(this).val(null).trigger('change')
                        $student.prop('disabled', true);
                        alert('Choose an ELA attendance to check')
                    } else {

                        // Allow input into the student name
                        $student.prop('disabled', false);
                    }
                } else if ($(this).val().length > 1) {
                    $(this).val(null).trigger('change')
                    $student.prop('disabled', true);
                    alert('Choose only one attendance to check')
                }
            }
        });
    };


    function renderHomework(subject, flavour){

        $('#js-assignment-choices').select2({
            theme: "bootstrap",

            placeholder: 'Homework',
            allowClear: true,
            ajax: {
                url: $('#js-assignment').attr('js-get-assignments-url'),
                async: true,
                type: "GET",
                dataType: 'json',
                data: {
                    'subject': subject,
                    'flavour': flavour
                    },
                success: function(result){
                    if(result.results == 'NO_GRADEBOOK'){
                        console.log(result.results)
                        var feedback = `No gradebook data for ${result.subject} has been uploaded yet!
                         \nTasks that you would assign to students are populated from the gradebook data.`
                        alert(feedback)
                    }
                    return result
                },
                error : function(xhr,errmsg,err) {
                    // Show an error & provide error detail to the console

                    console.log(xhr.status + ": " + xhr.responseText); // }
                }
            }
        })
    };


    function renderIspRadio(subject){
        //refreshRadios()
        $.ajax({
            url: $("#js-isp-options").attr('js-render-isp-radio-url'),
            async: true,
            type: "GET",
            data: {
                'subject': subject,
                },
            dataType: 'json',
            success: function(result){
                options = ""
                $.each(result, function () {
                    options += `<div class="form-check">
                    <input class="form-check-input" type="radio" name="js-isp-options"
                     id="${this.id}" value="${this.id}">
                    <label class="form-check-label" for="${this.id}">${this.display}</label>
                    </div>`
                    })
                $('#js-isp-options').append(options)
                $('#js-isps').show()

                // if the ISP option is selected or changed
                $('input[name="js-isp-options"]').change(function(){

                    // Empty any attendance options if an isp flavour is changed
                    $('#js-attendance-options').val(null).trigger('change')
                    // Need the subject code
                    var subtest = $('#js-subject-options').attr('js-one-subject')

                    var sub = subject
                    console.log(sub)
                    var flavour = $(this).val()
                    console.log(sub, subtest, flavour)
                    // Clear existing isp in tui editor
                    editor.setValue('');

                    // One subject has a length of 2,
                    if (sub.length != 2){
                        sub = $('input[name="js-subject-options"]:checked').val()
                    }
                    // Only care about attendance and homework if 2_a
                    if (flavour == '2_a'){
                        $student.prop('disabled', true);
                        renderAttendance(sub, flavour)
                        // Show the input
                        $("#js-attendance").show();

                        // Render the assignment choices
                        renderHomework(sub, flavour)
                        $('#js-assignment').show()
                        // Disable the student choice
                    } else {
                        $student.prop('disabled', false);
                    }

                });
            },
            error : function(xhr, errmsg, err) {

                // add error to the dom
                $('#js-results').html("<div class='alert-box alert radius' data-alert>"+
                "Oops! There has been an error.</div>");

                // Provide error detail to the console
                console.log(xhr.status + ": " + xhr.responseText);
            }
        })
    };


    function renderSubjectRadio(teacher){
        refreshRadios()

        $.ajax({
            url: $("#js-subject-options").attr('js-render-subject-radio-url'),
            async: true,
            type: "GET",
            data: {
                'teacher': teacher,
                },
            dataType: 'json',
            success: function(result){
                options = ""
                console.log(result.length)
                if (result.length > 1){
                    $.each(result, function () {
                        options += `<div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="js-subject-options"
                         id="${this.id}" value="${this.id}">
                        <label class="form-check-label" for="${this.id}">${this.display}</label>
                        </div>`
                    })
                    $('#js-subject-options').append(options).attr('js-one-subject','')
                    // show the subject choice options
                    // Once a subject choice has been made, the isp options radiobutton set can be generated
                    $('#js-subjects').show()
                    $('input[name="js-subject-options"]').change(function(){
                        // Changing subjects should reset the radios
                        $('#js-isp-options').empty()

                        // Empty any attendance options if a subject is changed
                        $('#js-attendance-options').val(null).trigger('change')
                        renderIspRadio($(this).val())
                    });
                } else {
                    $('#js-subjects').hide()
                    $('#js-subject-options').empty().attr('js-one-subject', result[0].id)
                    // Isp options can be rendered now
                    renderIspRadio(result[0].id)
                }
            },
            error : function(xhr,errmsg,err) {

                // add error to the dom
                $('#js-results').html("<div class='alert-box alert radius' data-alert>"+
                "Oops! There has been an error.</div>");
                // Provide error detail to the console
                console.log(xhr.status + ": " + xhr.responseText);
            }
        })
    }


    function makeTypeahead(selector, minLength){
        $(selector).typeahead({
            minLength: minLength,
            source: function (query, render) {
              Intercooler.triggerRequest($(selector), function (data) {
                render($.parseJSON(data));
              });
            },
            updater: function(pname){
                editor.setValue('')
                if (selector.includes('student')){
                    fillOutIsp(pname);
                } else {
                    $(selector).change(function(){

                        // So as not to confuse the logic in renderISP
                        $('#js-subject-options').attr('js-one-subject','')
                    })
                    renderSubjectRadio(pname);
                }
                return pname;
            }
        })
            //TODO What if a teacher that is not in the system wants to make an ISP?
            //.bind('typeahead:change', function(){
            //alert('did this work?');
            //})
    }

    // Instantiate teacher search typeahead
    makeTypeahead('#js-get-teachers', 3);

    // Instantiate student search typeahead
    makeTypeahead('#js-get-students', 2);


    // instantiate wysiwyg editor into which isp will be written
    // FIXME: Why does scrolling by the wysiwyg cause ugly embarrassing errors to be written to the console?
    var editor = new tui.Editor({
        el: document.querySelector('#js-tui-editor'),
        initialEditType: 'markdown',
        previewStyle: 'vertical',
        height: '600px',
        exts: ['scrollSync'],
    });


    // Instantiate clipboard into which generated isp will be copied
    var clipboard = new ClipboardJS('#js-clipper', {
        text: function(trigger) {
            var org = editor.getMarkdown()
            var enc = org.replace("^^ENCOURAGEMENT^^", $.trim($("#inspire").val()));
            console.log(enc, 'here')
            editor.setMarkdown(enc)
            return editor.getMarkdown()
        }}).on('success', function(e) {
            console.info('Action:', e.action);
            console.info('Text:', e.text);
            console.info('Trigger:', e.trigger);
            e.clearSelection();
            // TODO: post to student foundationyear email - Need another ajax view
            // TODO: Leverage We-chat api to post isp to student messaging app
            var win = window.open('https://myfy.foundationyear.com/', '_blank');
            if (win) {

                // Browser has allowed it to be opened
                win.focus();
            } else {

                // Browser has blocked it
                alert('Please allow popups for this website');
        }}).on('error', function(e) {
            console.error('Action:', e.action);
            console.error('Trigger:', e.trigger);
            alert('There was a problem copying the isp to the clipboard. You\'ll have to do it manually. Sorry!')
        });


    // TODO: This should be a typeahead like assignments
    /*
    $attendanceData.change(function(){
      if( $(this).val().length == 2 ){

        var choices = ['ELA', 'IELTS'];
        var attendOne = containsSubString($(this).val()[0], choices);
        var attendTwo = containsSubString($(this).val()[1], choices)
        if (attendOne != attendTwo){

            // Allow input into the student name
            $student.prop('disabled', false);
        } else {
            alert('Choose one each of ELA Attendance and IELTS Attendance')
            $(this)[0].selectedIndex = -1;
            $student.prop('disabled', true);
        }
      } else if ($(this).val().length > 2) {
        $(this)[0].selectedIndex = -1;
        alert('Choose ONE each of ELA Attendance and IELTS Attendance')
        $student.prop('disabled', true);
      }
    });
    */

    function fillOutIsp(student){

        // Give Feedback that something is happening
        $indicatorIsp.css("display", "block")
        //var attendance = $attendanceInput.val()
        try {
            var attendance = $('#js-attendance-options').select2('data')
            if (attendance.length == 2){
                var att1 = attendance[0].text
                var att2 = attendance[1].text
            } else {
                var att1 = attendance[0].text
                var att2 = ""
            }
        } catch(err) {
            var att1 = ""
            var att2 = ""
        }

        var subject = $('#js-subject-options').attr('js-one-subject')
        if (subject.length >1){
            var sub = subject
        } else {
            var sub = $('input[name="js-subject-options"]:checked').val()
        }
        $.ajax({
            url: $("#js-tui-editor").attr('js-fill-out-isp-url'),
            async: true,
            type: "GET",
            data: {
                'teacher': $('#js-get-teachers').val(),
                // TODO: subject from radio will be redundant on next iteration
                'subject': sub,
                'isp': $('input[name=js-isp-options]:checked').val(),
                'attendance_choice_one': att1,
                'attendance_choice_two': att2,
                'tasks': JSON.stringify($("#js-assignment-choices").val()),
                'student': student
                },
            dataType: 'json',
            success: function(result){

                // The something has finished happening; hide the feedback
                $indicatorIsp.css("display", "none")
                if(result.has_template){
                    editor.setMarkdown(result.template.join('\n'))
                } else {
                    alert(result.template)
                }
            },
            error : function(xhr,errmsg,err) {

                // add error to the dom
                $('#js-results').html("<div class='alert-box alert radius' data-alert>"+
                "Oops! There has been an error.</div>");
                // Provide error detail to the console
                console.log(xhr.status + ": " + xhr.responseText);
            }
        })
    }

});