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
integer, parameter :: k=kind(0)
integer(kind=k) :: i
i=99
associate(a_host_scope=>[77,(i,i=1_k,3_k),88])
call check_integer('host_scope:rank',rank(a_host_scope),1)
call check_integer('host_scope:size',size(a_host_scope),5)
call check_integer('host_scope:kind',kind(a_host_scope),k)
call check_integer('host_scope:value-1',a_host_scope(1),77)
call check_integer('host_scope:value-2',a_host_scope(2),1)
call check_integer('host_scope:value-3',a_host_scope(3),2)
call check_integer('host_scope:value-4',a_host_scope(4),3)
call check_integer('host_scope:value-5',a_host_scope(5),88)
end associate
call check_integer('host_i_after',i,99)
call finish_checks(9)
contains
end program p
