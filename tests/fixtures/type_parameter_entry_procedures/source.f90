program p
implicit none
integer :: checked
integer :: n,entries
checked=0
entries=0
n=2
call procedure_selector(n)
n=3
call procedure_entity(n)
call check_integer('procedures:entries',entries,2)
call finish_checks(9)
contains
subroutine procedure_selector(n)
integer, intent(inout) :: n
character(len=n) :: text
entries=entries+1
call check_integer('procedure_selector:entry',entries,1)
text='ab'
n=5
call check_integer('procedure_selector:source-now',n,5)
call check_integer('procedure_selector:length',len(text),2)
call check_logical('procedure_selector:payload',text=='ab',.true.)
end subroutine procedure_selector
subroutine procedure_entity(n)
integer, intent(inout) :: n
character :: text*(n)
entries=entries+1
call check_integer('procedure_entity:entry',entries,2)
text='abc'
n=7
call check_integer('procedure_entity:source-now',n,7)
call check_integer('procedure_entity:length',len(text),3)
call check_logical('procedure_entity:payload',text=='abc',.true.)
end subroutine procedure_entity
subroutine check_integer(label,actual,expected)
character(len=*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(len=*), intent(in) :: label
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
end program p
