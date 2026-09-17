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
program p
use enumeration_provider, only: public_kind, zebra_default, apple_default, &
    zebra_confirmed, apple_visible, exposed_apple
use enumeration_checks, only: check_integer, check_logical, finish_checks
implicit none
type(public_kind) :: public_value
public_value=apple_default
call check_integer('public-first',int(zebra_default),1)
call check_integer('public-second',int(apple_default),2)
call check_integer('confirmed-first',int(zebra_confirmed),1)
call check_integer('unmodified-second',int(apple_visible),2)
call check_integer('private-type-export',int(exposed_apple),2)
call check_logical('public-type-value',public_value==apple_default,.true.)
call check_integer('public-type-ordinal',int(public_value),2)
call finish_checks(7)
end program p
