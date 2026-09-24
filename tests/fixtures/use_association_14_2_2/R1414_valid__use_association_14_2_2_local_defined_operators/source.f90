! rule: R1414
! covers: local-defined-unary-operator local-defined-binary-operator
! evidence: effect
! standard: f2023
! oracle-basis: standard
module operator_rename_provider
  implicit none
  type :: box
    integer :: v
  end type
  interface operator(.addbox.)
    module procedure addbox
  end interface
  interface operator(.negbox.)
    module procedure negbox
  end interface
  interface operator(.wrongbox.)
    module procedure wrongbox
  end interface
  interface operator(.wrongneg.)
    module procedure wrongneg
  end interface
contains
  integer function addbox(left, right)
    type(box), intent(in) :: left, right
    addbox = 100 * left%v + right%v
  end function
  integer function negbox(value)
    type(box), intent(in) :: value
    negbox = -value%v
  end function
  integer function wrongbox(left, right)
    type(box), intent(in) :: left, right
    wrongbox = -999 - left%v - right%v
  end function
  integer function wrongneg(value)
    type(box), intent(in) :: value
    wrongneg = -999 - value%v
  end function
end module

program local_defined_operators
  use operator_rename_provider, only: box, operator(.localneg.) => operator(.negbox.), &
       operator(.localsum.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(5)
  right = box(4)
  if ((.localneg. left) /= -5) error stop 1
  if ((left .localsum. right) /= 504) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 LOCAL DEFINED OPERATORS OK'
end program
