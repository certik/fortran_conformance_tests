program p
implicit none
integer :: actual
actual = 83
call plain_out(actual)
if (actual /= 47) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE OUT PLAIN ENTRY OK'
contains
subroutine plain_out(x)
  integer, intent(out) :: x
  x = 47
end subroutine
end program p
