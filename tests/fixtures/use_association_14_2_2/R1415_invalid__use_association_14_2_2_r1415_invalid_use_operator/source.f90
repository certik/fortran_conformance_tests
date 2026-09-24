! rule: R1415
! covers: invalid-use-defined-operator-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1415_diag_provider
  type :: box; integer :: v; end type
  interface operator(.addbox.); module procedure addbox; end interface
contains
  integer function addbox(a,b); type(box),intent(in)::a,b; addbox=a%v+b%v; end function
end module
program r1415_invalid_use_operator
  use r1415_diag_provider, only: box, operator(.localadd.) => operator(+)
  implicit none
end program
