program p
implicit none
integer :: checked
integer :: n,entries,undefinition_calls
checked=0
entries=0
undefinition_calls=0
n=3
call undefined_procedure(n)
n=3
undefined_block: block
character(len=n) :: text
entries=entries+1
call check_integer('undefined_block:entry',entries,2)
text='abc'
call undefine(n)
call check_integer('undefined_block:length',len(text),3)
call check_logical('undefined_block:payload',text=='abc',.true.)
n=7
call check_integer('undefined_block:restored',n,7)
end block undefined_block
call check_integer('undefined:calls',undefinition_calls,2)
call check_integer('undefined:entries',entries,2)
call finish_checks(10)
contains
subroutine undefined_procedure(n)
integer, intent(inout) :: n
character(len=n) :: text
entries=entries+1
call check_integer('undefined_procedure:entry',entries,1)
text='abc'
call undefine(n)
call check_integer('undefined_procedure:length',len(text),3)
call check_logical('undefined_procedure:payload',text=='abc',.true.)
n=5
call check_integer('undefined_procedure:restored',n,5)
end subroutine undefined_procedure
subroutine undefine(x)
integer, intent(out) :: x
undefinition_calls=undefinition_calls+1
end subroutine undefine
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
