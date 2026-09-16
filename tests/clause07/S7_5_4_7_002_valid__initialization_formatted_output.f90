! rule: S7.5.4.7-002
! covers: formatted-inherited-order
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: parent
integer :: zed, alpha
end type
type, extends(parent) :: child
integer :: middle
end type
type(child) :: item
character(5) :: text
integer :: stat
item%zed=2
item%alpha=3
item%middle=5
write(text,'(I1,1X,I1,1X,I1)',iostat=stat) item
if (stat /= 0) error stop 1
if (text /= '2 3 5') error stop 2
end program
