jQuery (function($) {
  $(document).ready(function(){
      var order_by;
      if (POSITION == 'ministers') {
        order_by = [2, "desc"]
      }
      $('#mp-attendance').DataTable({
        "paging": false,
        "info": false,
        "order": order_by
      });
  });
});
