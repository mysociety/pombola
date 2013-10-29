;(function($) {
  $.fn.simpleTabs = function(options) {
    var opts = $.extend({}, $.fn.simpleTabs.defaults, options);

    return this.each(function() {
      var $this = $(this);

      var $links = $this.find(opts.linksSelector + ' a');
      var $panels = $this.find(opts.panelsSelector);

      $links.on('click', function(e) {
        e.preventDefault();

        // href of the clicked link is the id of the panel to show.
        var panelId = $(this).attr('href');

        // Update active link.
        $links.removeClass(opts.activeLinkClass);
        $(this).addClass(opts.activeLinkClass);

        // Update active panel.
        $panels.removeClass(opts.activePanelClass);
        $panels.filter(panelId).addClass(opts.activePanelClass);
      });
    })
  };

  // Default options, can be overridden by passing an options hash when
  // calling the plugin.
  $.fn.simpleTabs.defaults = {
    linksSelector: '.tab-links',
    panelsSelector: '.tab-content',
    activeLinkClass: 'active',
    activePanelClass: 'tab-active'
  };

  $(function() {
    $('.tabs').simpleTabs();
  });
})(jQuery);
