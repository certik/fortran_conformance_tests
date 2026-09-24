! rule: S19.3.1-005
! covers: generic-name-same-as-derived-type
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_generic_derived_type_mod
  implicit none
  type :: node
    integer :: v
  end type node
  interface node
    module procedure make_node
  end interface node
contains
  type(node) function make_node(x)
    integer, intent(in) :: x
    make_node%v = x + 70
  end function make_node
end module scoping_generic_derived_type_mod
program scoping_generic_derived_type
  use scoping_generic_derived_type_mod, only: node
  implicit none
  type(node) :: from_generic, from_constructor
  integer :: checks
  checks = 0
  from_generic = node(5)
  from_constructor = node(v=31)
  call expect_equal(from_generic%v, 75, 'generic name same as derived type')
  call expect_equal(from_constructor%v, 31, 'structure constructor keyword')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 GENERIC DERIVED TYPE OK'
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
end program scoping_generic_derived_type
