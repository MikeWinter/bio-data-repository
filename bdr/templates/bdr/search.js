/* globals Bloodhound */

jQuery(function ($) {
    "use strict";
    // Load the search engines used for matching query terms.
    var engine = new Bloodhound({
        remote: '{% url "bdr:search" %}?query=%QUERY',
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    });
    engine.initialize();
    var tags = new Bloodhound({
        remote: '{% url "bdr.frontend:tags" %}?filter=%QUERY',
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    });
    tags.initialize();

    var form = $('.repository-search');
    var selection = null;
    /*
     * The type-ahead functionality defined here and in the search engines
     * above provides suggestions based on dataset and tag names.
     */
    form.find('.form-control').typeahead({
        highlight: true,
        hint: true
    }, {
        source: engine.ttAdapter(),
        name: 'datasets',
        displayKey: 'name'
    }, {
        source: tags.ttAdapter(),
        name: 'tags',
        displayKey: 'name'
    });
    form.on('typeahead:autocompleted typeahead:selected', null, null,
        function (evt, suggestion, dataset) {
            selection = (dataset === 'datasets') ? suggestion : null;
        });
    /*
     * This search handler examines query matches derived from dataset names.
     * If only one name was found, this handler short circuits the search
     * results page and takes the user directly to the match.
     */
    form.submit(function (evt) {
        var term = this.elements.query.value;
        var search = true;
        // Only process non-empty, non-default search terms.
        if (term && selection && selection.href && (term !== this.elements.query.defaultValue) &&
                (selection.name.toLowerCase() === term.toLowerCase())) {
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
