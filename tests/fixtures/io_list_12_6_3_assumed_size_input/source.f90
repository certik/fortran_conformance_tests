subroutine io_list_assumed_size_input(a)
  implicit none
  integer :: a(*)
  character(len=1) :: rec
  rec = '5'
  read(rec,*) a
end subroutine io_list_assumed_size_input
