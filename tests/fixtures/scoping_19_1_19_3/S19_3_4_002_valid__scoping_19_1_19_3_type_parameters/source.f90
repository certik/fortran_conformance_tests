! rule: S19.3.4-002
! covers: type-parameter-name-type-definition-scope type-parameter-keyword-use type-parameter-inquiry-use
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_type_parameters
  implicit none
  integer, parameter :: default_k = kind(0)
  type :: box(k)
    integer, kind :: k
    integer(kind=k) :: value
  end type box
  type(box(k=default_k)) :: b
  integer :: k, checks
  k = 99
  checks = 0
  b%value = 123
  call expect_equal(b%k, default_k, 'type parameter inquiry')
  call expect_equal(kind(b%value), default_k, 'type parameter definition scope')
  call expect_equal(int(b%value), 123, 'component value')
  call expect_equal(k, 99, 'outer k unchanged')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 TYPE PARAMETERS OK'
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
end program scoping_type_parameters
