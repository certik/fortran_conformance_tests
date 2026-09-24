module attribute_8_5_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_true, finish_checks
contains
subroutine fail(label)
character(*), intent(in) :: label
print *, 'CHECK_FAILED', label
error stop 99
end subroutine fail
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
print *, 'CHECK_INT', label, actual, expected
error stop 1
end if
checked = checked + 1
end subroutine check_int
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) call fail(label)
checked = checked + 1
end subroutine check_true
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, expected
error stop 2
end if
end subroutine finish_checks
end module attribute_8_5_checks
module c816_result_shapes
implicit none
contains
function fixed_result() result(r)
integer :: r(2,3)
integer :: i, j
do j = 1, 3
  do i = 1, 2
    r(i,j) = 10*i + j
  end do
end do
end function fixed_result
function sized_result(n) result(r)
integer, intent(in) :: n
integer :: r(n)
integer :: i
do i = 1, n
  r(i) = 100 + i
end do
end function sized_result
end module c816_result_shapes
program p
use attribute_8_5_checks
use c816_result_shapes
implicit none
call check_true('c816-explicit-list-shape', all(shape(fixed_result()) == [2,3]))
call check_true('c816-specification-bound-shape', all(shape(sized_result(4)) == [4]))
call finish_checks(2)
end program p
