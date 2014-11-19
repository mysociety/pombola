(function ($) {
  function hideOrShowContent(useRaw) {
    if (useRaw) {
      $('.field-markdown_content').hide();
      $('.field-raw_content').show();
    } else {
      $('.field-markdown_content').show();
      $('.field-raw_content').hide();
    }
  }

  $(function () {
    var useRawCheckboxSelector = 'input#id_use_raw',
        useRawCheckbox = $(useRawCheckboxSelector),
        useRaw = useRawCheckbox.prop('checked');
        hideOrShowContent(useRaw);
    useRawCheckbox.on('change', function(e) {
      hideOrShowContent(e.target.checked);
    });
  });
})(django.jQuery);

