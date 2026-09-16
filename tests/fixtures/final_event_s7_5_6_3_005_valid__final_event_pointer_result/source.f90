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
final :: finish_scalar
end type item
type(item), target, save :: saved_target
contains
subroutine finish_scalar(self)
type(item), intent(inout) :: self
call record_event(10,self%token)
end subroutine finish_scalar
impure function locate() result(value)
type(item), pointer :: value
value=>saved_target
call record_event(5,23)
end function locate
impure integer function consume(value) result(answer)
type(item), intent(in) :: value
! checkpoint: pointer-getter
call expect_log([5],[23])
answer=value%token
call record_event(20,answer)
end function consume
end module final_types
program p
use final_types
use final_log, only: reset_log, record_event, expect_log, expect_before
implicit none
integer :: status
integer :: answer
call reset_log()
saved_target%token=23
answer=consume(locate())
! checkpoint: pointer-after
call expect_log([5,20],[23,23])
if (answer/=23) error stop 147
saved_target=item(token=29)
! checkpoint: pointer-positive
call expect_log([5,20,10],[23,23,23])
if (saved_target%token/=29) error stop 148
end program p
