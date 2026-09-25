program io_list_input_implied_do_expression_control
  implicit none
  integer :: a(2), i
  character(len=3) :: rec
  rec = '1 2'
  a = -9
  read(rec,*) (a(i), i = 1, 2)
end program io_list_input_implied_do_expression_control
