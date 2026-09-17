program p
implicit none
integer :: checked
integer :: n,procedure_entries,block_entries,iteration
checked=0
procedure_entries=0
block_entries=0
n=2
call capture_fresh(n)
n=4
call capture_fresh(n)
call check_integer('fresh:procedure-count',procedure_entries,2)
do iteration=1,2
if (iteration==1) then
n=3
else
n=5
end if
reentered: block
character(len=n) :: text
block_entries=block_entries+1
select case(block_entries)
case(1)
call check_integer('fresh_block_first:entry',block_entries,1)
text='abc'
n=7
call check_integer('fresh_block_first:source-now',n,7)
call check_integer('fresh_block_first:length',len(text),3)
call check_logical('fresh_block_first:payload',text=='abc',.true.)
case(2)
call check_integer('fresh_block_second:entry',block_entries,2)
text='abcde'
n=7
call check_integer('fresh_block_second:source-now',n,7)
call check_integer('fresh_block_second:length',len(text),5)
call check_logical('fresh_block_second:payload',text=='abcde',.true.)
case default
print *, 'UNEXPECTED_ENTRY','block',block_entries
error stop 4
end select
end block reentered
end do
call check_integer('fresh:block-count',block_entries,2)
call finish_checks(18)
contains
subroutine capture_fresh(n)
integer, intent(inout) :: n
character(len=n) :: text
procedure_entries=procedure_entries+1
select case(procedure_entries)
case(1)
call check_integer('fresh_procedure_first:entry',procedure_entries,1)
text='ab'
n=7
call check_integer('fresh_procedure_first:source-now',n,7)
call check_integer('fresh_procedure_first:length',len(text),2)
call check_logical('fresh_procedure_first:payload',text=='ab',.true.)
case(2)
call check_integer('fresh_procedure_second:entry',procedure_entries,2)
text='abcd'
n=7
call check_integer('fresh_procedure_second:source-now',n,7)
call check_integer('fresh_procedure_second:length',len(text),4)
call check_logical('fresh_procedure_second:payload',text=='abcd',.true.)
case default
print *, 'UNEXPECTED_ENTRY','procedure',procedure_entries
error stop 4
end select
end subroutine capture_fresh
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
