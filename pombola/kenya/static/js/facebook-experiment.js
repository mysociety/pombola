var logbookUrl = 'http://logbook.mysociety.org/mzalendo-fb';

// http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function recordPageHit(pageName) {
    var sid = getParameterByName('sid');
    if (sid != null) {
        // Fire off some AJAX to record this click.
        $.ajax({
            url: logbookUrl,
            data: {
                sid: sid,
                action: 'page_view',
                value: pageName
            }
        });
    }
}

function loadPageInteractivity() {

    // Show the hidden page element (we don't show anything if no JS is available)
    $('#ctas').show();

    var options = {
        placeholder: 'Constituency',
        allowClear: true
    }

    var matcherObject = {matcher: includeOptgroupsMatcher};
    var optionsWithGroupMatcherNarrow = $.extend({}, matcherObject, options);
    var iebcSelector = $('.iebc-office-lookup select');

    var sid = getParameterByName('sid');

    // Do the IEBC office selector magic
    iebcSelector.select2(optionsWithGroupMatcherNarrow);
    iebcSelector.on("select2:select", function(e) {
        e.preventDefault();

        $.ajax({
            url: "/iebc-office-ajax",
            data: {
                area: iebcSelector.val()
            },
            type: "GET",
            dataType: "html",
            success: function (data) {
                $('#constituency-lookup-result').html(data);
            },
            error: function (xhr, status) {
                $('#constituency-lookup-result').html('<p>Sorry, we were unable to get your constituency details. Please try again.</p>');
            }
        });

        // Do we have a SID?
        if (sid != null) {
            // Fire off some AJAX to record this
            $.ajax({
                url: logbookUrl,
                data: {
                    sid: sid,
                    action: 'page_interaction',
                    value: 'select_constituency'
                }
            });
        }

    });

    // JS to detect selection of a favourite network
    $('.js-show-preferred-social').on('change', function(){
        var network = $(this).val();
        if(network != '') {
            $('.js-show-preferred-social-thanks').show();
        } else {
            $('.js-show-preferred-social-thanks').hide();
        }

        // Do we have a SID?
        if (sid != null) {
            // Fire off some AJAX to record this click.
            $.ajax({
                url: logbookUrl,
                data: {
                    sid: sid,
                    action: 'page_interaction',
                    value: 'select_social_network'
                }
            });
        }
    });

    if (sid != null) {
        var pageTimer = 0;
        setInterval(function(){
            // Only run this tick if the page is actually visible
            if (!document.hidden) {
                pageTimer += 10;
                $.ajax({
                    url: logbookUrl,
                    data: {
                        sid: sid,
                        action: 'page_time',
                        value: pageTimer
                    }
                });
            }
        }, 10000);
    }

}
