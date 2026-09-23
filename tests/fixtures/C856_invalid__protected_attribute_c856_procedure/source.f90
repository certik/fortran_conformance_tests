subroutine local_owner()
  implicit none
  integer, protected :: x
end subroutine
program main
  implicit none
  call local_owner()
  write(*,'(a)') 'PROTECTED ATTRIBUTE C856 PROCEDURE CONTROL OK'
end program
