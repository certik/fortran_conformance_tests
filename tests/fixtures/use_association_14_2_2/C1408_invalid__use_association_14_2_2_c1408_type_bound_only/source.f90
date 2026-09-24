! rule: C1408
! covers: only-type-bound-generic-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1408_type_bound_provider
  type :: box
    integer :: v
  contains
    procedure :: addbox
    generic :: operator(.addbox.) => addbox
  end type
contains
  integer function addbox(a,b); class(box),intent(in)::a; type(box),intent(in)::b; addbox=a%v+b%v; end function
end module
program c1408_type_bound_only
  use c1408_type_bound_provider, only: box, operator(.addbox.)
  implicit none
end program
