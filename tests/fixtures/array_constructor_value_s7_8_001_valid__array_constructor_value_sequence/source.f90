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
integer :: m(2,2)
m(1,1)=11
m(2,1)=13
m(1,2)=17
m(2,2)=19
call check_integer('scalars:size',size([11,13,17]),3)
call observe_scalars([11,13,17])
call check_integer('matrix:size',size([5,m,23]),6)
call observe_matrix([5,m,23])
call finish_checks(15)
contains
subroutine observe_scalars(a)
integer, intent(in) :: a(..)
call check_integer('scalars:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('scalars:argument-size',size(a),3)
call check_integer('scalars:value-1',a(1),11)
call check_integer('scalars:value-2',a(2),13)
call check_integer('scalars:value-3',a(3),17)
rank default
print *, 'UNEXPECTED_RANK','scalars',rank(a)
error stop 4
end select
end subroutine observe_scalars
subroutine observe_matrix(a)
integer, intent(in) :: a(..)
call check_integer('matrix:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('matrix:argument-size',size(a),6)
call check_integer('matrix:value-1',a(1),5)
call check_integer('matrix:value-2',a(2),11)
call check_integer('matrix:value-3',a(3),13)
call check_integer('matrix:value-4',a(4),17)
call check_integer('matrix:value-5',a(5),19)
call check_integer('matrix:value-6',a(6),23)
rank default
print *, 'UNEXPECTED_RANK','matrix',rank(a)
error stop 4
end select
end subroutine observe_matrix
end program p
