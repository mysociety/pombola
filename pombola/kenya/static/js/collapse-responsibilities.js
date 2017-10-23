jQuery(function($){
    var maxNumberOfChildren = 5;
    var hiddenClass = 'ui-helper-hidden-accessible';

    $('.js-collapse-responsibilities').each(function(){
        var $parent = $(this);
        var $children = $parent.find('li, p');
        var $tooManyChildren = $children.slice(maxNumberOfChildren);

        if ($tooManyChildren.length) {
            $tooManyChildren.addClass(hiddenClass);
            $('<button>')
                .text(
                    'Show ' + $tooManyChildren.length + ' more ' + 
                    ($tooManyChildren.length > 1 ? 'responsibilities' : 'responsibility')
                )
                .appendTo($parent)
                .on('click', function(){
                    $tooManyChildren.removeClass(hiddenClass);
                    $(this).remove();
                });
        }
    });
});
