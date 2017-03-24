window.blazy = new Blazy({
    selector: 'img[data-src]'
});

$(document).on('js-mp-profiles-live-filter:updated', function(){
    window.blazy.revalidate();
});
