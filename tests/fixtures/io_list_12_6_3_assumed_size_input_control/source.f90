subroutine io_list_assumed_size_input_control(a)
  implicit none
  integer :: a(*)
  character(len=1) :: rec
  rec = '5'
  read(rec,*) a(1)
end subroutine io_list_assumed_size_input_control
