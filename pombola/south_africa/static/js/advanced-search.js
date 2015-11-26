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

    $('.datepicker').datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: "yy-mm-dd",
    });

    // The "Update results" button is disabled by default...
    var $advancedUpdateButton = $('.js-update-results-button');
    $advancedUpdateButton.prop('disabled', true);

    // And then activated again once they change any of the settings...
    var $advancedOptions = $('.js-update-results-trigger');
    $('input, select', $advancedOptions).on('change', function(){
        $advancedUpdateButton.prop('disabled', false);
    });
});
