module final_log
implicit none
private
integer, parameter :: capacity=64
integer, save :: nlog=0
integer, save :: log_kind(capacity)=0, log_token(capacity)=0
public :: record_event, reset_log, expect_log, expect_before
contains
subroutine reset_log()
nlog=0
log_kind=0
log_token=0
end subroutine reset_log
subroutine record_event(kind,token)
integer, intent(in) :: kind,token
if (nlog >= capacity) error stop 101
nlog=nlog+1
log_kind(nlog)=kind
log_token(nlog)=token
end subroutine record_event
subroutine report_actual()
integer :: i
print *, 'ACTUAL_COUNT',nlog
do i=1,nlog
print *, 'ACTUAL_EVENT',log_kind(i),log_token(i)
end do
end subroutine report_actual
subroutine expect_log(kinds,tokens)
integer, intent(in) :: kinds(:),tokens(:)
integer :: i
if (size(kinds) /= size(tokens)) error stop 102
if (nlog /= size(kinds)) then
call report_actual()
error stop 103
end if
do i=1,size(kinds)
if (count(log_kind(1:nlog)==kinds(i) .and. log_token(1:nlog)==tokens(i)) /= &
    count(kinds==kinds(i) .and. tokens==tokens(i))) then
call report_actual()
error stop 104
end if
end do
end subroutine expect_log
subroutine expect_before(left_kind,left_token,right_kind,right_token)
integer, intent(in) :: left_kind,left_token,right_kind,right_token
integer :: i,last_left,first_right
last_left=0
first_right=nlog+1
do i=1,nlog
if (log_kind(i)==left_kind .and. log_token(i)==left_token) last_left=i
if (log_kind(i)==right_kind .and. log_token(i)==right_token) first_right=min(first_right,i)
end do
if (last_left==0 .or. first_right==nlog+1) then
call report_actual()
error stop 105
end if
if (last_left>=first_right) then
call report_actual()
error stop 106
end if
end subroutine expect_before
end module final_log
module final_types
use final_log, only: record_event, expect_log, expect_before
implicit none
type :: item
integer :: token
contains
final :: finish_array
end type item
integer, save :: array_finals=0
contains
subroutine finish_array(self)
type(item), intent(inout) :: self(:)
integer :: i
array_finals=array_finals+1
call record_event(30,size(self))
do i=1,size(self)
call record_event(31,self(i)%token)
end do
end subroutine finish_array
impure elemental subroutine define_out(self,new_token)
type(item), intent(out) :: self
integer, intent(in) :: new_token
if (array_finals/=0) error stop 155
call record_event(20,new_token)
self%token=new_token
end subroutine define_out
end module final_types
program p
use final_types
use final_log, only: reset_log, record_event, expect_log, expect_before
implicit none
integer :: status
type(item), allocatable :: actual(:)
call reset_log()
allocate(actual(2),stat=status)
if (status/=0) error stop 111
if (.not.allocated(actual)) error stop 112
actual(1)%token=17
actual(2)%token=19
call define_out(actual,[31,37])
! checkpoint: array-only-after-call
call expect_log([20,20],[31,37])
if (array_finals/=0) error stop 156
if (any(actual%token/=[31,37])) error stop 157
if (.not.allocated(actual)) error stop 113
deallocate(actual,stat=status)
if (status/=0) error stop 114
if (allocated(actual)) error stop 115
! checkpoint: array-only-cleanup
call expect_log([20,20,30,31,31],[31,37,2,31,37])
if (array_finals/=1) error stop 158
end program p
