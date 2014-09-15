jQuery(function($) {
    var $searchResultsOrder = $('#search-results-order');
    $('.radio-button-columns input:radio').change(function() {
        var section = $(this).val();

        // In advanced search, order Hansard and Questions by date, everything
        // else by relevance.
        if (section === 'hansard' || section === 'questions') {
            $searchResultsOrder.val('date');
        } else {
            $searchResultsOrder.val('relevance');
        }
    });
});
