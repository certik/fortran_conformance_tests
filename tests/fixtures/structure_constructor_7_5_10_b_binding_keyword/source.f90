! rule: C7106
! covers: binding-is-not-component
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_binding_mod
implicit none
type :: gadget
  integer :: payload
contains
  procedure :: get
end type gadget
contains
integer function get(self)
  class(gadget), intent(in) :: self
  get = self%payload
end function get
end module sc_b_binding_mod
program structure_constructor_7_5_10_b_binding_keyword
use sc_b_binding_mod
implicit none
type(gadget) :: value
value = gadget(payload=11, get=19)
end program structure_constructor_7_5_10_b_binding_keyword
