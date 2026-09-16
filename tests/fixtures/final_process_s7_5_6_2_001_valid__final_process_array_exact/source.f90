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
type :: item
integer :: token
contains
final :: finish_vector
final :: finish_matrix
end type item
contains
subroutine finish_vector(self)
type(item), intent(inout) :: self(:)
integer :: i
call record_event(10,size(self))
do i=1,size(self)
call record_event(11,self(i)%token)
end do
end subroutine finish_vector
subroutine finish_matrix(self)
type(item), intent(inout) :: self(:,:)
integer :: i,j
call record_event(20,size(self))
do j=1,size(self,2)
do i=1,size(self,1)
call record_event(21,self(i,j)%token)
end do
end do
end subroutine finish_matrix
end module final_types
program p
use final_types
use final_log, only: reset_log, expect_log, expect_before
implicit none
integer :: status
type(item), allocatable :: vector(:),matrix(:,:)
call reset_log()
allocate(vector(2),stat=status)
if (status/=0) error stop 111
if (.not.allocated(vector)) error stop 112
vector(1)%token=17
vector(2)%token=19
if (.not.allocated(vector)) error stop 113
deallocate(vector,stat=status)
if (status/=0) error stop 114
if (allocated(vector)) error stop 115
call expect_log([10,11,11],[2,17,19])
call reset_log()
allocate(matrix(2,2),stat=status)
if (status/=0) error stop 111
if (.not.allocated(matrix)) error stop 112
matrix(1,1)%token=23
matrix(2,1)%token=29
matrix(1,2)%token=31
matrix(2,2)%token=37
if (.not.allocated(matrix)) error stop 113
deallocate(matrix,stat=status)
if (status/=0) error stop 114
if (allocated(matrix)) error stop 115
call expect_log([20,21,21,21,21],[4,23,29,31,37])
call reset_log()
allocate(vector(0),stat=status)
if (status/=0) error stop 111
if (.not.allocated(vector)) error stop 112
if (.not.allocated(vector)) error stop 113
deallocate(vector,stat=status)
if (status/=0) error stop 114
if (allocated(vector)) error stop 115
call expect_log([10],[0])
end program p
