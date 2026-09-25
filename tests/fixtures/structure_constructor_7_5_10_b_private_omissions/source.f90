! rule: C7107
! covers: omitted-private-default, omitted-private-allocatable
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_private_mod
implicit none
private
public :: default_box, alloc_box, observe_default_box, observe_alloc_box
type :: default_box
  integer, public :: tag
  integer, private :: hidden = 17
end type default_box
type :: alloc_box
  integer, public :: tag
  integer, allocatable, private :: store(:)
end type alloc_box
contains
subroutine observe_default_box(x)
  type(default_box), intent(in) :: x
  if (x%tag /= 29) error stop 1
  if (x%hidden /= 17) error stop 2
end subroutine observe_default_box
subroutine observe_alloc_box(x)
  type(alloc_box), intent(in) :: x
  if (x%tag /= 31) error stop 3
  if (allocated(x%store)) error stop 4
end subroutine observe_alloc_box
end module sc_b_private_mod
program structure_constructor_7_5_10_b_private_omissions
use sc_b_private_mod
implicit none
call observe_default_box(default_box(tag=29))
call observe_alloc_box(alloc_box(tag=31))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PRIVATE OMISSIONS OK'
end program structure_constructor_7_5_10_b_private_omissions
