program io_list_input_nonvariable_control
  implicit none
  character(len=1) :: rec
  integer :: x
  rec = '7'
  x = -7
  read(rec,*) x
end program io_list_input_nonvariable_control
