subroutine save_bare_scope()
  implicit none
  integer :: x
  save
  x = 12
  if (x /= 12) error stop 1
end subroutine
program main
  implicit none
  call save_bare_scope()
  write(*,'(a)') 'ATTRIBUTE STATEMENTS SAVE C893 CONTROL OK'
end program
