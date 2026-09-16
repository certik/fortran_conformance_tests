! rule: S7.5.4.6-006
! covers: integer-kind-conversion
! evidence: effect
! standard: f2023
program component_witness
implicit none
integer, parameter :: ik=selected_int_kind(18)
type :: record
integer :: value=3_ik
end type
type(record) :: item
if (item%value /= 3) error stop 1
call verify(item%value)
contains
subroutine verify(value)
integer(kind(0)), intent(in) :: value
if (value /= 3) error stop 2
end subroutine
end program
