/**
 * Created by: Michael Winter (mail@michael-winter.me.uk)
 *       Date: 2015-10-20
 */

jQuery(function ($) {
    "use strict";
    var operations = {UNKNOWN: 1, SAVE: 2, TEST: 3};
    var invalidPattern =
        '<p class="text-danger">\n' +
        '    <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>\n' +
        '    Invalid pattern.\n' +
        '</p>\n';
    var mapsTo =
        '<div id="mapped-to" class="form-group">\n' +
        '    <label class="control-label col-xs-3">Maps to</label>\n' +
        '    <div class="col-xs-9">\n' +
        '        <p class="form-control-static">$mapped_to</p>\n' +
        '    </div>\n' +
        '</div>\n';
    var matchFeedback =
        '<span class="form-control-feedback glyphicon $classes"\n' +
        '      role="status" aria-hidden="true" style="right: 4em"></span>\n';
    var matchText = '<span class="sr-only" role="status">($text)</span>\n';
    var form = $('#filter-form');

    if (!form) {
        return;
    }

    $('button[type=submit]', form).each(function (idx, elem) {
        $(elem).click(function (evt) {
            switch (evt.target.value) {
                case "save":
                    form.data('op', operations.SAVE);
                    break;
                case "test":
                    form.data('op', operations.TEST);
                    break;
                default:
                    form.data('op', operations.UNKNOWN);
                    break;
            }
        });
    });

    function showMapping(re, element) {
        var filename = element.value;
        if (re.test(filename)) {
            var mapping = element.form.elements.mapping.value;
            if (mapping) {
                mapping = mapping.replace(/(\\+)(\d+)/g, function (match, slashes, digits) {
                    if (slashes.length % 2 === 0) {
                        return match;
                    }
                    return slashes.substring(0, slashes.length - 1) + '$' + digits;
                });
                mapping = filename.replace(re, mapping);
            } else {
                mapping = filename;
            }
            addPositiveFeedback(element, [
                matchFeedback.replace('$classes', 'glyphicon-ok'),
                matchText.replace('$text', 'matches')
            ]);
            $(element).closest('.form-group').after(mapsTo.replace('$mapped_to', mapping));
        } else {
            addNegativeFeedback(element, [
                matchFeedback.replace('$classes', 'glyphicon-remove'),
                matchText.replace('$text', 'does not match')
            ]);
        }
    }

    function validatePattern(element) {
        var re = null;
        resetFeedback(element);
        try {
            re = new RegExp(element.value, 'g');
            addPositiveFeedback(element);
        } catch (exc) {
            addNegativeFeedback(element, invalidPattern);
        }
        return re;
    }

    function addPositiveFeedback(element, content) {
        addFeedback(element, content, 'has-success');
    }

    function addNegativeFeedback(element, content) {
        addFeedback(element, content, 'has-error');
    }

    function addFeedback(element, content, classNames) {
        $(element).closest('.form-group').addClass(classNames);
        if (content) {
            $(element).after(content);
        }
    }

    function resetFeedback(element) {
        $(element).closest('.form-group').removeClass('has-success has-error').addClass(
            'has-feedback');
        $(element).parent().children('p.text-danger').remove();
        $(element).parent().children('[role=status]').remove();
    }

    form.submit(function (evt) {
        var patternElement = this.elements.pattern;
        var filenameElement = this.elements.filename;
        resetFeedback(filenameElement);
        $('#mapped-to').remove();

        var re = validatePattern(patternElement);
        if (re) {
            if (form.data('op') !== operations.TEST) {
                return true;
            }

            showMapping(re, filenameElement);
        }

        if (evt.preventDefault) {
            evt.preventDefault();
        }
        return false;
    });
});
