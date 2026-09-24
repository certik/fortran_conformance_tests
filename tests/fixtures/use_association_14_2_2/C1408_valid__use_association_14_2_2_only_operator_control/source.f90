! rule: C1408
! covers: only-generic-nontype-bound-control
! evidence: effect
! standard: f2023
! oracle-basis: standard
module operator_provider
  implicit none
  type :: box
    integer :: v
  end type
  interface operator(.addbox.)
    module procedure addbox
  end interface
contains
  integer function addbox(left, right)
    type(box), intent(in) :: left, right
    addbox = 100 * left%v + right%v
  end function
end module
program operator_control
  use operator_provider, only: box, operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(2)
  right = box(7)
  if ((left .addbox. right) /= 207) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 OPERATOR CONTROL OK'
end program
