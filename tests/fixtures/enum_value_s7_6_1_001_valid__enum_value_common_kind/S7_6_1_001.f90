module enum_value_observer
implicit none
private
public :: check_definition
contains
subroutine check_definition(tag,actual,expected,kind_agrees)
integer, intent(in) :: tag,actual(:),expected(:)
logical, intent(in) :: kind_agrees
if (size(actual)/=size(expected)) then
print *, 'ENUM_SIZE_MISMATCH',tag
error stop 101
end if
if (size(actual)==0) then
print *, 'ENUM_EMPTY_OBSERVATION',tag
error stop 102
end if
if (any(actual/=expected)) then
print *, 'ENUM_VALUE_MISMATCH',tag
print *, actual
error stop 104
end if
if (.not.kind_agrees) then
print *, 'ENUM_KIND_MISMATCH',tag
error stop 105
end if
end subroutine check_definition
end module enum_value_observer
program enum_values
use enum_value_observer, only: check_definition
implicit none
enum, bind(c)
enumerator :: common_zero,common_one,common_four=4
enumerator :: common_five,common_nine=9,common_ten
end enum
! definition: common
call check_definition(1, &
    [int(common_zero),int(common_one),int(common_four),int(common_five), &
     int(common_nine),int(common_ten)], &
    [0,1,4,5,9,10], &
    all([kind(common_zero),kind(common_one),kind(common_four),kind(common_five), &
     kind(common_nine),kind(common_ten)] == kind(common_zero)))
end program enum_values
