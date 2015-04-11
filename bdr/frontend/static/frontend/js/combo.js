jQuery(function ($) {
    var comboFields = $('select[datatype~="combobox"]');

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
        return $(element).next('input[datatype~="combobox"]');
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
