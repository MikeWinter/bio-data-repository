jQuery(function ($) {
    "use strict";
    var comboFields = $('select[data-type~="combobox"]');

    function changeHandler(evt) {
        var textField = getDependentField(this);

        if (this.value !== '') {
            textField.prop('disabled', true);
            textField.hide();
        } else {
            textField.prop('disabled', false);
            textField.show();
        }
    }

    function getDependentField(element) {
        return $(element).next('input[data-type~="combobox"]');
    }

    $.each(comboFields, function (index, element) {
        $(element).change(changeHandler);

        if (element.value !== '') {
            var textField = getDependentField(element);

            textField.prop('disabled', true);
            textField.hide();
        }
    });
});
