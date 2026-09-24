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
module c817_module_specification_part
implicit none
integer, public :: c817_admitted_public = 41
integer, private :: c817_admitted_private = 43
end module c817_module_specification_part
program p
use attribute_8_5_checks
use c817_module_specification_part
implicit none
integer :: c817_admitted_private = 143
call check_int('c817-module-public-access-spec', c817_admitted_public, 41)
call check_int('c817-module-private-access-spec', c817_admitted_private, 143)
call finish_checks(2)
end program p
