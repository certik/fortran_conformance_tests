! rule: S19.3.1-003
! covers: external-function-defining-subprogram-exception
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_function_exception
  implicit none
  interface
    integer function scope_result(n)
      integer, intent(in) :: n
    end function scope_result
  end interface
  integer :: checks
  checks = 0
  call expect_equal(scope_result(5), 47, 'external function name in defining subprogram')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 FUNCTION EXCEPTION OK'
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
end program scoping_function_exception
integer function scope_result(n)
  implicit none
  integer, intent(in) :: n
  scope_result = -90
  scope_result = 42 + n
end function scope_result
