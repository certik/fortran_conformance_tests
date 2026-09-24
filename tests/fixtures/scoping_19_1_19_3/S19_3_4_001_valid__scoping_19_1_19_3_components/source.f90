! rule: S19.3.4-001
! covers: component-name-type-definition-scope component-name-designator-use component-keyword-structure-constructor-use
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_components
  implicit none
  type :: type_one
    integer :: tag = -123
    integer :: other = -456
  end type type_one
  type :: type_two
    integer :: tag = -222
  end type type_two
  type(type_one) :: left, obj, built
  type(type_two) :: right
  integer :: tag, selected, mixed_sum, checks
  tag = 99
  checks = 0
  left%tag = 11
  left%other = 101
  right%tag = 22
  obj%tag = 31
  selected = obj%tag
  built = type_one(tag=44)
  mixed_sum = left%tag + right%tag
  call expect_equal(left%tag, 11, 'type one component')
  call expect_equal(right%tag, 22, 'type two component')
  call expect_equal(mixed_sum, 33, 'per-type component names')
  call expect_equal(selected, 31, 'component designator')
  call expect_equal(built%tag, 44, 'constructor keyword tag')
  call expect_equal(tag, 99, 'outer tag unchanged')
  call expect_equal(checks, 6, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 COMPONENTS OK'
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
end program scoping_components
