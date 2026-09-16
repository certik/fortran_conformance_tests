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
contains
subroutine finish_array(self)
type(item), intent(inout) :: self(:)
integer :: i
call record_event(10,size(self))
do i=1,size(self)
call record_event(11,self(i)%token)
end do
end subroutine finish_array
end module final_types
program p
use final_types
use final_log, only: reset_log, record_event, expect_log, expect_before
implicit none
integer :: status
type(item), allocatable :: left(:)
call reset_log()
allocate(left(2),stat=status)
if (status/=0) error stop 111
if (.not.allocated(left)) error stop 112
left(1)%token=7
left(2)%token=11
! checkpoint: reallocation-before
call expect_log([integer ::],[integer ::])
left=[item(token=17),item(token=19),item(token=23)]
if (.not.allocated(left)) error stop 125
if (size(left)/=3) error stop 126
if (any(left%token/=[17,19,23])) error stop 127
! checkpoint: reallocation-assigned
call expect_log([10,11,11],[2,7,11])
if (.not.allocated(left)) error stop 113
deallocate(left,stat=status)
if (status/=0) error stop 114
if (allocated(left)) error stop 115
! checkpoint: reallocation-cleanup
call expect_log([10,11,11,10,11,11,11],[2,7,11,3,17,19,23])
end program p
