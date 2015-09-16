/* globals Bloodhound */

jQuery(function ($) {
    "use strict";
    // Load the search engines used for matching query terms.
    var tags = new Bloodhound({
        remote: {
            url: '{% url "bdr:tags" %}?query=%QUERY',
            wildcard: '%QUERY'
        },
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    });
    tags.initialize();

    var datasets = new Bloodhound({
        remote: {
            url: '{% url "bdr:datasets" %}?query=%QUERY',
            wildcard: '%QUERY'
        },
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    });
    datasets.initialize();

    var form = $('.repository-search');
    var selection = null;
    /*
     * The type-ahead functionality defined here and in the search engines
     * above provides suggestions based on dataset and tag names.
     */
    form.find('.form-control').typeahead({
        highlight: true,
        hint: true,
        minLength: 2
    }, {
        source: tags.ttAdapter(),
        name: 'tags',
        display: function (suggestion) {
            return '#' + suggestion.name;
        }
    }, {
        source: datasets.ttAdapter(),
        name: 'datasets',
        display: 'name'
    });
    /*
     * Remember the selected suggestion for examination during submission.
     */
    form.on('typeahead:autocomplete typeahead:select', null, null,
        function (evt, suggestion) {
            selection = suggestion;
        });
    /*
     * This search handler examines query matches derived from dataset names.
     * If only one name was found, this handler short circuits the search
     * results page and takes the user directly to the match.
     */
    form.submit(function (evt) {
        var term = (this.elements.query.value || "").toLowerCase();
        var search = true;
        // Only process non-empty, non-default search terms.
        if (term && selection && selection.href &&
                (term !== this.elements.query.defaultValue.toLowerCase()) &&
                ($.inArray(selection.name.toLowerCase(), [term, '#' + term]) !== -1)) {
            search = false;
            location.href = selection.href;
        }
        // Cancel form submission if the destination has already been found.
        if (!search && evt.preventDefault) {
            evt.preventDefault();
        }
        return search;
    });
});
