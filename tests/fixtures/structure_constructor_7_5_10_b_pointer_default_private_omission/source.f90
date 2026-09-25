! rule: S7.5.10-005
! covers: pointer-default-source-use, private-omission-source-use
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_default_mod
implicit none
private
public :: record, observe_record, default_target
integer, target, save :: default_target = 41
type :: record
  integer, public :: tag
  integer, pointer, public :: p => null()
  integer, private :: hidden = 17
  integer, allocatable, private :: store(:)
end type record
contains
subroutine observe_record(x)
  type(record), intent(in) :: x
  if (x%tag /= 29) error stop 1
  if (associated(x%p)) error stop 2
  if (x%hidden /= 17) error stop 3
  if (allocated(x%store)) error stop 4
end subroutine observe_record
end module sc_b_default_mod
program structure_constructor_7_5_10_b_pointer_default_private
use sc_b_default_mod
implicit none
call observe_record(record(tag=29))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR POINTER DEFAULT PRIVATE OMIT OK'
end program structure_constructor_7_5_10_b_pointer_default_private
