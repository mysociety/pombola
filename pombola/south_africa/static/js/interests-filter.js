jQuery (function($) {
    $('#display').change(function() {
        if ($('#display').val()!='all') {
            $('#organisation').prop( "disabled", true );
            $('#party').prop( "disabled", true );
        }
        else {
            $('#organisation').prop( "disabled", false );
            $('#party').prop( "disabled", false );
        }
    });
    $('#display').trigger("change");

    $('.group-select').on('click', function() {
        $('#group-interests-form').submit();
    });
});
