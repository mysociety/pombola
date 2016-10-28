"use strict";

var logbookUrl = "http://logbook.mysociety.org/mzalendo-fb";

// http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
function getParameterByName(name, url) {
    if (!url) {
        url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) {
        return null;
    }
    if (!results[2]) {
        return "";
    }
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

// Send a Logbook message!
function asyncSendLogbook(sid, action, value, on_complete) {
    if (value === undefined) {
        value = null;
    }
    if (on_complete === undefined) {
        on_complete = function () { return; };
    }
    if (sid !== null) {
        // Fire off some AJAX to record this click.
        $.ajax({
            url: logbookUrl,
            data: {
                sid: sid,
                action: action,
                value: value
            },
            timeout: 1000,
            complete: on_complete
        });
    } else {
        // No SID, but we still need to do whatever action should be taken.
        on_complete();
    }
}

function recordPageHit(pageName) {
    var sid = getParameterByName("sid");
    asyncSendLogbook(sid, "page_view", pageName);
}

function loadPageInteractivity() {

    var sid = getParameterByName("sid");

    // Show the hidden page elements (we don"t show anything if no JS is available)
    $(".js-hidden-content").show();

    // Magic to intercept tagged hyperlinks
    $("a[data-logbooktag]").click(function (event) {
        event.preventDefault();
        asyncSendLogbook(sid,
            "link_click",
            $(event.target).data("logbooktag"),
            function () {
                window.location.href = $(event.target).attr("href");
            }
        );
        return false;
    });

    /*
     * CONSTITUENCY SELECT ON POLITICAL PAGE
     */

    var options = {
            placeholder: "Constituency",
            allowClear: true
        },
        matcherObject = {matcher: includeOptgroupsMatcher},
        optionsWithGroupMatcherNarrow = $.extend({}, matcherObject, options),
        iebcSelector = $(".iebc-office-lookup select");

    // Do the IEBC office selector magic
    iebcSelector.select2(optionsWithGroupMatcherNarrow);
    iebcSelector.on("select2:select", function (e) {
        e.preventDefault();

        $.ajax({
            url: "/iebc-office-ajax",
            data: {
                area: iebcSelector.val()
            },
            type: "GET",
            dataType: "html",
            success: function (data) {
                $("#constituency-lookup-result").html(data);
            },
            error: function (xhr, status) {
                $("#constituency-lookup-result").html("<p>Sorry, we were unable to get your constituency details. Please try again.</p>");
            }
        });

        asyncSendLogbook(sid, "page_interaction", "select_constituency");

    });

    /*
     * FUNCTIONS FOR DOING QUIZZY THINGS
     */

    var quizzes = {
        "number-of-mps": {
            "answer": "350",
            "answer_string": "That's right!"
        },
        "parliament-governor-oversight": {
            "answer": "no",
            "answer_string": "That's right!"
        },
        "ocean-coverage": {
            "answer": "71",
            "answer_string": "That's right, a huge 361.9 million km²."
        },
        "mariana-trench": {
            "answer": "pacific",
            "answer_string": "Yes! Only three people have ever been to the deepest part of the world's oceans."
        },
        "indian-ocean-deepest": {
            "answer": "diamantina-deep",
            "answer_string": "Yes! The Diamantina Deep is 8,047m deep."
        }
    };

    $.each(quizzes, function (name, params) {
        $("#quiz_" + name).on("change", function () {
            var answer = $(this).val();
            if (answer !== "") {
                if (answer === params.answer) {
                    $("#quiz_" + name + "_answer").html(params.answer_string);
                } else {
                    $("#quiz_" + name + "_answer").html("Sorry, that's not right. Why not try again?");
                }
                $("#quiz_" + name + "_answer").show();
            } else {
                $("#quiz_" + name + "_answer").hide();
            }

            asyncSendLogbook(sid, "page_interaction", name);

        });
    });

    /*
     * TIME ON PAGE
     */

    if (sid !== null) {
        var pageTimer = 0;
        setInterval(function () {
            // Only run this tick if the page is actually visible
            if (!document.hidden) {
                pageTimer += 10;
                asyncSendLogbook(sid, "page_time", pageTimer);
            }
        }, 10000);
    }

}
