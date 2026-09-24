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
module s852_implicit_default
implicit none
integer :: implicit_public = 31
end module s852_implicit_default
module s852_nolist_public
implicit none
public
integer :: no_list_public = 37
end module s852_nolist_public
module s852_nolist_private
implicit none
private
integer :: no_list_private = 41
end module s852_nolist_private
module s852_explicit_public_module
implicit none
private
public :: explicit_public
integer :: explicit_public = 43
end module s852_explicit_public_module
module s852_explicit_private_module
implicit none
public
private :: explicit_private
integer :: explicit_private = 47
end module s852_explicit_private_module
module s852_origin_default
implicit none
integer, public :: origin_default = 53
end module s852_origin_default
module s852_middle_default
use s852_origin_default, only: imported_default => origin_default
implicit none
private
end module s852_middle_default
program p
use attribute_8_5_checks
use s852_implicit_default
use s852_nolist_public
use s852_nolist_private
use s852_explicit_public_module
use s852_explicit_private_module
use s852_middle_default
implicit none
integer :: no_list_private = 141, explicit_private = 147, imported_default = 153
call check_int('s852-implicit-public-local', implicit_public, 31)
call check_int('s852-no-list-public', no_list_public, 37)
call check_int('s852-no-list-private-local', no_list_private, 141)
call check_int('s852-explicit-public-in-private-default', explicit_public, 43)
call check_int('s852-explicit-private-in-public-default', explicit_private, 147)
call check_int('s852-use-associated-local-default', imported_default, 153)
call finish_checks(6)
end program p
