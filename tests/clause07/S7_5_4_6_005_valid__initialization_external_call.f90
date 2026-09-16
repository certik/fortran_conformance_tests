! rule: S7.5.4.6-005
! covers: external-target-call
! evidence: effect
! standard: f2023
module external_types
implicit none
abstract interface
  integer function calculation(x)
    integer, intent(in) :: x
  end function
end interface
procedure(calculation) :: outside
type :: record
  procedure(calculation), pointer, nopass :: action => outside
end type
end module
integer function outside(x)
implicit none
integer, intent(in) :: x
outside = x+3
end function
program external_witness
use external_types
implicit none
type(record) :: item
if (.not.associated(item%action,outside)) error stop 1
if (item%action(4) /= 7) error stop 2
end program
