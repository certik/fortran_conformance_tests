! rule: R1415
! covers: use-defined-unary-operator use-defined-binary-operator
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

program use_defined_operators
  use operator_rename_provider, only: box, operator(.myneg.) => operator(.negbox.), &
       operator(.myadd.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(6)
  right = box(3)
  if ((.myneg. left) /= -6) error stop 1
  if ((left .myadd. right) /= 603) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 USE DEFINED OPERATORS OK'
end program
