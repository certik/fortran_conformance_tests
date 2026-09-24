! rule: C1407
! covers: rename-type-bound-generic-operator-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1407_type_bound_provider
  type :: box
    integer :: v
  contains
    procedure :: addbox
    generic :: operator(.addbox.) => addbox
  end type
contains
  integer function addbox(a,b); class(box),intent(in)::a; type(box),intent(in)::b; addbox=a%v+b%v; end function
end module
program c1407_type_bound_rename
  use c1407_type_bound_provider, only: box, operator(.localadd.) => operator(.addbox.)
  implicit none
end program
