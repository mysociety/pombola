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

$(function(){

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
                url: '/fb/ajax/record',
                data: {
                    sid: sid,
                    qid: '54',
                    selid: '10165'
                }
            });
        }

    });

    // Show/hide the comparison table
    $('.js-compare-countries').on('click', function(){
        $('.js-compare-countries-result table').toggle();

        // Do we have a SID?
        if (sid != null) {
            // Fire off some AJAX to record this click.
            $.ajax({
                url: '/fb/ajax/record',
                data: {
                    sid: sid,
                    qid: '56',
                    selid: '10168'
                }
            });
        }

    });

    // JS to swap the winners on the Olympics page
    $('.js-show-winners').on('change', function(){
        var year = $(this).val();
        if(year != '') {
            $('.js-show-winners-result #' + year).show().siblings().hide();
        } else {
            $('.js-show-winners-result table').hide();
        }

        // Do we have a SID?
        if (sid != null) {
            // Fire off some AJAX to record this click.
            $.ajax({
                url: '/fb/ajax/record',
                data: {
                    sid: sid,
                    qid: '57',
                    selid: '10169'
                }
            });
        }
    });

    if (sid != null) {
        var pageTimer = 0;
        setInterval(function(){
            pageTimer += 10;
            $.ajax({
                url: '/fb/ajax/value',
                data: {
                    sid: sid,
                    qid: '64',
                    value: pageTimer
                }
            });
        }, 15000);
    }

});
