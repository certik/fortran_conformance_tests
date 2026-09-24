! rule: R1414
! covers: invalid-local-defined-operator-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1414_diag_provider
  type :: box; integer :: v; end type
  interface operator(.addbox.); module procedure addbox; end interface
contains
  integer function addbox(a,b); type(box),intent(in)::a,b; addbox=a%v+b%v; end function
end module
program r1414_invalid_local_operator
  use r1414_diag_provider, only: box, operator(+) => operator(.addbox.)
  implicit none
end program
