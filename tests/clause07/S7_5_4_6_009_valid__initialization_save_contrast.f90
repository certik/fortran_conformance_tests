! rule: S7.5.4.6-009
! covers: unsaved-local-reentry explicit-save-control
! evidence: effect
! standard: f2023
module save_types
implicit none
type :: record
  integer :: value=3
end type
end module
program save_witness
use save_types
implicit none
call visit(1)
call visit(2)
contains
subroutine visit(iteration)
  integer, intent(in) :: iteration
  type(record) :: automatic
  type(record), save :: persistent
  if (automatic%value /= 3) error stop 1
  if (iteration == 1) then
    if (persistent%value /= 3) error stop 2
  else
    if (persistent%value /= 9) error stop 3
  end if
  automatic%value=9
  persistent%value=9
end subroutine
end program
