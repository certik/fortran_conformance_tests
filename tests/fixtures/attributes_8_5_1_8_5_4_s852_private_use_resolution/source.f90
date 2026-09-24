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
module s8523_private_data_provider
implicit none
private :: hidden_data
integer :: hidden_data = 61
end module s8523_private_data_provider
module s8523_proc_provider
implicit none
private :: hidden_proc, hidden_gen
interface hidden_gen
  module procedure provider_gen_int
end interface hidden_gen
contains
integer function hidden_proc()
hidden_proc = 71
end function hidden_proc
integer function provider_gen_int(x)
integer, intent(in) :: x
provider_gen_int = x + 80
end function provider_gen_int
end module s8523_proc_provider
module s8523_origin
implicit none
integer, public :: origin_reexp = 91
end module s8523_origin
module s8523_reexport_middle
use s8523_origin, only: reexp => origin_reexp
implicit none
private :: reexp
end module s8523_reexport_middle
program p
use attribute_8_5_checks
use s8523_private_data_provider
use s8523_proc_provider
use s8523_reexport_middle
implicit none
integer :: hidden_data = 161, reexp = 171
interface hidden_gen
  procedure local_gen_int
end interface hidden_gen
call check_int('s8523-private-data-name-fallback', hidden_data, 161)
call check_int('s8523-private-procedure-name-fallback', hidden_proc(), 191)
call check_int('s8523-private-generic-identifier-fallback', hidden_gen(5), 205)
call check_int('s8523-private-reexport-fallback', reexp, 171)
call finish_checks(4)
contains
integer function hidden_proc()
hidden_proc = 191
end function hidden_proc
integer function local_gen_int(x)
integer, intent(in) :: x
local_gen_int = x + 200
end function local_gen_int
end program p
