module enumeration_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, finish_checks
contains
subroutine check_integer(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'ORDINAL',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'RELATION',label,'ACTUAL',actual,'EXPECTED',expected
error stop 2
end if
checked=checked+1
end subroutine check_logical
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked/=expected) then
print *, 'CHECK_COUNT',checked,'EXPECTED',expected
error stop 3
end if
end subroutine finish_checks
end module enumeration_checks
module enumeration_construction
use enumeration_checks, only: check_integer, check_logical
implicit none
enumeration type :: selection_kind
enumerator :: zulu_pick, alpha_pick, mango_pick
end enumeration type selection_kind
type(selection_kind), parameter :: fixed_middle=selection_kind(2)
contains
subroutine observe_selection(label,actual,expected,expected_ordinal)
character(*), intent(in) :: label
type(selection_kind), intent(in) :: actual,expected
integer, intent(in) :: expected_ordinal
call check_logical(label//':member',actual==expected,.true.)
call check_integer(label//':ordinal',int(actual),expected_ordinal)
end subroutine observe_selection
end module enumeration_construction
program p
use enumeration_construction, only: selection_kind, zulu_pick, alpha_pick, mango_pick, &
    fixed_middle, observe_selection
use enumeration_checks, only: finish_checks
implicit none
type(selection_kind) :: value
integer :: index
value=selection_kind(1)
call observe_selection('first',value,zulu_pick,1)
value=selection_kind(2)
call observe_selection('interior',value,alpha_pick,2)
value=selection_kind(3)
call observe_selection('last',value,mango_pick,3)
index=2
value=selection_kind(index)
call observe_selection('dynamic-second',value,alpha_pick,2)
index=3
value=selection_kind(index)
call observe_selection('dynamic-third',value,mango_pick,3)
call observe_selection('constant',fixed_middle,alpha_pick,2)
index=2
call observe_selection('scalar-result',selection_kind(index),alpha_pick,2)
call finish_checks(14)
end program p
