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
module s852_declaration_subjects
implicit none
integer, public :: list_public_a = 11, list_public_b = 13
integer, private :: list_private_a = 17, list_private_b = 19
type, public :: exported_t
  integer :: n = 23
end type exported_t
type, private :: hidden_t
  integer :: n = 29
end type hidden_t
end module s852_declaration_subjects
program p
use attribute_8_5_checks
use s852_declaration_subjects
implicit none
integer :: list_private_a = 117, list_private_b = 119
type :: hidden_t
  integer :: n = 129
end type hidden_t
type(exported_t) :: exported_object
type(hidden_t) :: hidden_object
call check_true('s852-declaration-list-public-names', all([list_public_a, list_public_b] == [11,13]))
call check_true('s852-declaration-list-private-fallbacks', all([list_private_a, list_private_b] == [117,119]))
call check_int('s852-derived-type-public-name', exported_object%n, 23)
call check_int('s852-derived-type-private-fallback', hidden_object%n, 129)
call finish_checks(4)
end program p
