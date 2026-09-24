! rule: S19.5.1.6-001
! covers: select-type-establishes-selector-association
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_construct_select_type
  implicit none
  type :: parent
    integer :: v
  end type parent
  type, extends(parent) :: child
  end type child
  class(parent), allocatable :: poly
  integer :: checks
  allocate(child :: poly)
  poly%v = 1
  checks = 0
  select type (a => poly)
  type is (child)
    a%v = 42
    call expect_equal(poly%v, 42, 'select type associate-to-selector')
    poly%v = 77
    call expect_equal(a%v, 77, 'select type selector-to-associate')
  class default
    error stop 'wrong dynamic type'
  end select
  call expect_equal(poly%v, 77, 'select type final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT SELECT TYPE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_select_type
