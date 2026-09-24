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
module r807_forms
implicit none
integer, public :: r807_public_value = 17
integer, private :: r807_private_value = 23
type, public :: r807_public_type
  integer :: n = 31
end type r807_public_type
type, private :: r807_private_type
  integer :: n = 37
end type r807_private_type
end module r807_forms
program p
use attribute_8_5_checks
use r807_forms
implicit none
integer :: r807_private_value = 61
type :: r807_private_type
  integer :: n = 67
end type r807_private_type
type(r807_public_type) :: public_object
type(r807_private_type) :: private_object
call check_int('r807-public-form-value', r807_public_value, 17)
call check_int('r807-private-form-fallback-value', r807_private_value, 61)
call check_int('r807-public-form-type', public_object%n, 31)
call check_int('r807-private-form-type-fallback', private_object%n, 67)
call finish_checks(4)
end program p
