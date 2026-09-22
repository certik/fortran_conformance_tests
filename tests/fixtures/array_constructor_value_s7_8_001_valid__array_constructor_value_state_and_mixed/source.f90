module array_value_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, finish_checks
contains
subroutine check_integer(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'CHECK_LOGICAL',label,'ACTUAL',actual,'EXPECTED',expected
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
end module array_value_checks
program p
use array_value_checks, only: check_integer, check_logical, finish_checks
implicit none
integer, target :: backing(2)
integer, pointer :: ptr(:)
integer, allocatable :: alloc(:)
integer :: one(1), empty(0), three(3)
backing(1)=41
backing(2)=43
ptr=>backing
allocate(alloc(2))
alloc(1)=47
alloc(2)=53
one(1)=61
three(1)=73
three(2)=79
three(3)=83
associate(a_mixed=>[one,empty,three])
call check_integer('mixed:rank',rank(a_mixed),1)
call check_integer('mixed:size',size(a_mixed),4)
call check_integer('mixed:value-1',a_mixed(1),61)
call check_integer('mixed:value-2',a_mixed(2),73)
call check_integer('mixed:value-3',a_mixed(3),79)
call check_integer('mixed:value-4',a_mixed(4),83)
end associate
associate(a_state=>[ptr,alloc])
call check_integer('state:rank',rank(a_state),1)
call check_integer('state:size',size(a_state),4)
call check_integer('state:value-1',a_state(1),41)
call check_integer('state:value-2',a_state(2),43)
call check_integer('state:value-3',a_state(3),47)
call check_integer('state:value-4',a_state(4),53)
end associate
call finish_checks(12)
contains
end program p
