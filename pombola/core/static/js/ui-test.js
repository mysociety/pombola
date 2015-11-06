jQuery(function($) {

  $('.ui-test-datepicker').datepicker({
    changeMonth: true,
    changeYear: true,
    dateFormat: "yy-mm-dd",
    maxDate: 0,
    beforeShow: function(){
      $('.ui-test-datepicker-show').attr('disabled', true);
      $('.ui-test-datepicker-hide').attr('disabled', false);
    },
    onClose: function(){
      $('.ui-test-datepicker-show').attr('disabled', false);
      $('.ui-test-datepicker-hide').attr('disabled', true);
    }
  });

  $('.ui-test-datepicker-show').on('click', function(){
    $('.ui-test-datepicker').datepicker('show');
  });

  $('.ui-test-datepicker-hide').on('click', function(){
    $('.ui-test-datepicker').datepicker('close');
  });

  $('.ui-test-autocomplete').autocomplete({
    source: [
      {"name": "Alice Grey", "image_url": "http://api.adorable.io/avatars/140/alice"},
      {"name": "Bob Green", "image_url": "http://api.adorable.io/avatars/140/bob"},
      {"name": "Carol Pink", "image_url": "http://api.adorable.io/avatars/140/carol"},
      {"name": "Dave Brown", "image_url": "http://api.adorable.io/avatars/140/dave"},
      {"name": "Eve White", "image_url": "http://api.adorable.io/avatars/140/eve"},
      {"name": "Frank Black", "image_url": "http://api.adorable.io/avatars/140/frank"}
    ],
    delay: 0,
    minLength: 0,
    open: function(){
      $('.ui-test-autocomplete-show').attr('disabled', true);
      $('.ui-test-autocomplete-hide').attr('disabled', false);
    },
    close: function(){
      $('.ui-test-autocomplete-show').attr('disabled', false);
      $('.ui-test-autocomplete-hide').attr('disabled', true);
    }
  }).on('focus', function(){
    $(this).autocomplete('search');
  }).data('uiAutocomplete')._renderItem = function(ul, item) {
    var itemElement = $('<li>'), imageElement = $('<img>');
    imageElement.attr({
      src: item.image_url,
      width: 16,
      height: 16
    });
    itemElement.append(imageElement).append(' ' + item.name);
    return itemElement.appendTo(ul);
  };

  $('.ui-test-autocomplete-show').on('click', function(){
    $('.ui-test-autocomplete').autocomplete('search');
  });

  $('.ui-test-autocomplete-hide').on('click', function(){
    $('.ui-test-autocomplete').autocomplete('close');
  });

  $(".ui-test-tabs").tabs().on("tabsactivate", function(event, ui) {
    history.pushState(null, null, '#' + ui.newPanel[0].id);
  });

  $('.ui-test-dialog').dialog({
    open: function(){
      var $instance = $('.ui-test-dialog').dialog('instance');
      $('.ui-test-dialog-wrapper').css({
        width: $instance.uiDialog.outerWidth(),
        height: $instance.uiDialog.outerHeight()
      });
      $('.ui-test-dialog-show').attr('disabled', true);
      $('.ui-test-dialog-hide').attr('disabled', false);
    },
    close: function(){
      $('.ui-test-dialog-show').attr('disabled', false);
      $('.ui-test-dialog-hide').attr('disabled', true);
    },
    position: {
      my: "left top",
      at: "left top",
      of: ".ui-test-dialog-wrapper"
    },
    modal: $('.ui-test-dialog-modal').is(':checked')
  });

  $('.ui-test-dialog-show').on('click', function(){
    $('.ui-test-dialog').dialog('open');
  });

  $('.ui-test-dialog-hide').on('click', function(){
    $('.ui-test-dialog').dialog('close');
  });

  $('.ui-test-dialog-modal').on('change', function(){
    var $dialog = $('.ui-test-dialog');
    $dialog.dialog('option', 'modal', $(this).is(':checked'));
    if($dialog.dialog('isOpen')){
      $dialog.dialog('close').dialog('open');
    }
  });

  $(document).on('click', '.ui-widget-overlay', function(){
    $('.ui-test-dialog').dialog('close');
  });

});
