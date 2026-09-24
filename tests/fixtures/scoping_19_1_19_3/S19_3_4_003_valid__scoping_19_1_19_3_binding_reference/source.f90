! rule: S19.3.4-003
! covers: binding-name-type-definition-scope binding-name-procedure-reference-use
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_binding_reference_mod
  implicit none
  private
  public :: box
  type :: box
    integer :: base
  contains
    procedure :: calc => calc_impl
  end type box
contains
  integer function calc_impl(self)
    class(box), intent(in) :: self
    calc_impl = self%base + 4
  end function calc_impl
  integer function wrong_calc_impl(self)
    class(box), intent(in) :: self
    wrong_calc_impl = self%base + 31
  end function wrong_calc_impl
end module scoping_binding_reference_mod
program scoping_binding_reference
  use scoping_binding_reference_mod, only: box
  implicit none
  type(box) :: obj
  integer :: calc, checks
  obj%base = 60
  calc = 99
  checks = 0
  call expect_equal(obj%calc(), 64, 'type-bound binding reference')
  call expect_equal(calc, 99, 'outer calc unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 BINDING REFERENCE OK'
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
end program scoping_binding_reference
