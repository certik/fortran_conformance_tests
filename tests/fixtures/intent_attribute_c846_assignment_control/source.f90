program p
implicit none
integer :: actual
actual = 19
call define_inout(actual)
if (actual /= 5) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE C846 ASSIGNMENT CONTROL OK'
contains
subroutine define_inout(x)
  integer, intent(inout) :: x
  x = 5
end subroutine
end program p
