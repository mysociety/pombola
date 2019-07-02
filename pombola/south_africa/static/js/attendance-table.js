jQuery (function($) {
  $(document).ready(function(){
      var order_by;
      if (POSITION == 'ministers') {
        order_by = [3, "desc"]
      }
      $('#mp-attendance').DataTable({
        "paging": false,
        "info": false,
        "order": order_by
      });
  });
});
