/*
Biological Dataset Repository: data archival and retrieval.
Copyright (C) 2015  Michael Winter

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

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
