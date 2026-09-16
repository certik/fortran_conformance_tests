! rule: S7.5.4.6-006
! covers: integer-kind-conversion
! evidence: effect
! standard: f2023
program component_witness
implicit none
integer, parameter :: ik=selected_int_kind(18)
type :: record
integer(ik) :: value=3
end type
type(record) :: item
if (item%value /= 3) error stop 1
call verify(item%value)
contains
subroutine verify(value)
integer(ik), intent(in) :: value
if (value /= 3) error stop 2
end subroutine
end program
