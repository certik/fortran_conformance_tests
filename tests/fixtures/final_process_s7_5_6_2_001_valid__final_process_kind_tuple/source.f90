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
use final_log, only: record_event
implicit none
type :: item(ka,kb,n,m)
integer, kind :: ka,kb
integer, len :: n,m
integer :: token
contains
final :: finish_11
final :: finish_12
final :: finish_21
final :: finish_22
end type item
contains
subroutine finish_11(self)
type(item(ka=1,kb=1,n=*,m=*)), intent(inout) :: self
call record_event(101,self%token)
call record_event(901,self%n)
call record_event(902,self%m)
end subroutine finish_11
subroutine finish_12(self)
type(item(ka=1,kb=2,n=*,m=*)), intent(inout) :: self
call record_event(102,self%token)
call record_event(901,self%n)
call record_event(902,self%m)
end subroutine finish_12
subroutine finish_21(self)
type(item(ka=2,kb=1,n=*,m=*)), intent(inout) :: self
call record_event(201,self%token)
call record_event(901,self%n)
call record_event(902,self%m)
end subroutine finish_21
subroutine finish_22(self)
type(item(ka=2,kb=2,n=*,m=*)), intent(inout) :: self
call record_event(202,self%token)
call record_event(901,self%n)
call record_event(902,self%m)
end subroutine finish_22
end module final_types
program p
use final_types
use final_log, only: reset_log, expect_log, expect_before
implicit none
integer :: status
type(item(ka=1,kb=1,n=3,m=5)), allocatable :: a
type(item(ka=1,kb=2,n=7,m=9)), allocatable :: b
type(item(ka=2,kb=1,n=4,m=6)), allocatable :: c
type(item(ka=2,kb=2,n=8,m=10)), allocatable :: d
type(item(ka=1,kb=1,n=12,m=14)), allocatable :: e
call reset_log()
call reset_log()
allocate(a,stat=status)
if (status/=0) error stop 111
if (.not.allocated(a)) error stop 112
a%token=11
if (.not.allocated(a)) error stop 113
deallocate(a,stat=status)
if (status/=0) error stop 114
if (allocated(a)) error stop 115
call expect_log([101,901,902],[11,3,5])
call reset_log()
allocate(b,stat=status)
if (status/=0) error stop 111
if (.not.allocated(b)) error stop 112
b%token=13
if (.not.allocated(b)) error stop 113
deallocate(b,stat=status)
if (status/=0) error stop 114
if (allocated(b)) error stop 115
call expect_log([102,901,902],[13,7,9])
call reset_log()
allocate(c,stat=status)
if (status/=0) error stop 111
if (.not.allocated(c)) error stop 112
c%token=17
if (.not.allocated(c)) error stop 113
deallocate(c,stat=status)
if (status/=0) error stop 114
if (allocated(c)) error stop 115
call expect_log([201,901,902],[17,4,6])
call reset_log()
allocate(d,stat=status)
if (status/=0) error stop 111
if (.not.allocated(d)) error stop 112
d%token=19
if (.not.allocated(d)) error stop 113
deallocate(d,stat=status)
if (status/=0) error stop 114
if (allocated(d)) error stop 115
call expect_log([202,901,902],[19,8,10])
call reset_log()
allocate(e,stat=status)
if (status/=0) error stop 111
if (.not.allocated(e)) error stop 112
e%token=23
if (.not.allocated(e)) error stop 113
deallocate(e,stat=status)
if (status/=0) error stop 114
if (allocated(e)) error stop 115
call expect_log([101,901,902],[23,12,14])
end program p
