
  $(function() {
    return $('#main_search_box').autocomplete({
      source: "/autocomplete",
      minLength: 2,
      select: function(event, ui) {
        if (ui.item) return window.location = ui.item.url;
      }
    });
  });
