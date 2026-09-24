! rule: S19.3.4-004
! covers: nongeneric-spec-generic-binding-accessible-scope
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_generic_binding_operator_mod
  implicit none
  private
  public :: box
  type :: box
    integer :: v
  contains
    procedure :: add_box
    procedure :: wrong_add_box
    generic :: operator(+) => add_box
  end type box
contains
  type(box) function add_box(left, right)
    class(box), intent(in) :: left
    type(box), intent(in) :: right
    add_box%v = left%v * 10 + right%v
  end function add_box
  type(box) function wrong_add_box(left, right)
    class(box), intent(in) :: left
    type(box), intent(in) :: right
    wrong_add_box%v = left%v + right%v
  end function wrong_add_box
end module scoping_generic_binding_operator_mod
program scoping_generic_binding_operator
  use scoping_generic_binding_operator_mod, only: box
  implicit none
  type(box) :: left, right, combined
  integer :: checks
  checks = 0
  left%v = 6
  right%v = 7
  combined = left + right
  call expect_equal(combined%v, 67, 'generic binding operator plus')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 GENERIC BINDING OPERATOR OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_generic_binding_operator
