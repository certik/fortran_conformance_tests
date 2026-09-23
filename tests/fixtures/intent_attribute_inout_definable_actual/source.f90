program p
implicit none
integer :: actual
actual = 61
call retain_inout(actual)
if (actual /= 61) error stop 1
call write_inout(actual)
if (actual /= 73) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE INOUT DEFINABLE ACTUAL OK'
contains
subroutine retain_inout(x)
  integer, intent(inout) :: x
  if (x /= 61) error stop 3
end subroutine
subroutine write_inout(x)
  integer, intent(inout) :: x
  x = 73
end subroutine
end program p
