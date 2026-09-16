! rule: S7.5.4.7-001
! covers: formatted-input-order
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: record
integer :: zed, alpha
integer :: middle
end type
type(record) :: item
character(5) :: text
integer :: stat
text='7 4 1'
read(text,'(I1,1X,I1,1X,I1)',iostat=stat) item
if (stat /= 0) error stop 1
if (item%zed /= 7 .or. item%alpha /= 4 .or. item%middle /= 1) error stop 2
end program
