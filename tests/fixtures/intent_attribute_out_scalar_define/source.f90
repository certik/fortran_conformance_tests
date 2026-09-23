program p
implicit none
integer :: actual
actual = 29
call define_out(actual)
if (actual /= 47) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE OUT SCALAR DEFINE OK'
contains
subroutine define_out(x)
  integer, intent(out) :: x
  x = 47
end subroutine
end program p
