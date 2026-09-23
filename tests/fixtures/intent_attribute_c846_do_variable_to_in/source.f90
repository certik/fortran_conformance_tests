program p
implicit none
integer :: actual
integer :: marker
actual = 19
call local_do_control(actual, marker)
if (actual /= 19) error stop 1
if (marker /= 3) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE C846 DO VARIABLE INVALID OK'
contains
subroutine local_do_control(i, marker)
  integer, intent(in) :: i
  integer, intent(out) :: marker
  integer :: j
  marker = 0
  do i = 1, 3
    marker = marker + 1
  end do
end subroutine
end program p
