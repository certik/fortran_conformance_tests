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
module enumeration_list
implicit none
enumeration type :: list_kind
enumerator :: zephyr, amber, maple
end enumeration type list_kind
end module enumeration_list
module enumeration_split
implicit none
enumeration type :: split_kind
enumerator :: walrus
enumerator :: banana, quail
end enumeration type split_kind
end module enumeration_split
module enumeration_single
implicit none
enumeration type :: single_kind
enumerator :: only_value
end enumeration type single_kind
end module enumeration_single
program p
use enumeration_list, only: zephyr, amber, maple
use enumeration_split, only: walrus, banana, quail
use enumeration_single, only: only_value
use enumeration_checks, only: check_integer, check_logical, finish_checks
implicit none
call check_integer('list-first',int(zephyr),1)
call check_integer('list-second',int(amber),2)
call check_integer('list-third',int(maple),3)
call check_integer('split-first',int(walrus),1)
call check_integer('split-second',int(banana),2)
call check_integer('split-third',int(quail),3)
call check_logical('list-order',zephyr<amber .and. amber<maple,.true.)
call check_logical('list-reverse',maple<zephyr,.false.)
call check_logical('split-order',walrus<banana .and. banana<quail,.true.)
call check_logical('split-reverse',quail<walrus,.false.)
call check_integer('single-ordinal',int(only_value),1)
call check_logical('single-huge-value',huge(only_value)==only_value,.true.)
call check_integer('single-huge-ordinal',int(huge(only_value)),1)
call check_logical('list-last-value',huge(zephyr)==maple,.true.)
call check_integer('list-last-ordinal',int(huge(zephyr)),3)
call finish_checks(15)
end program p
