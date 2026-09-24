! rule: R1411
! covers: rename-defined-operator-form
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

program rename_defined_operator
  use operator_rename_provider, only: box, operator(.localadd.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(2)
  right = box(7)
  if ((left .localadd. right) /= 207) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RENAME DEFINED OPERATOR OK'
end program
