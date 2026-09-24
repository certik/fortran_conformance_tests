! rule: S19.3.3-001
! covers: function-statement-result-exists function-result-name-class-one-local
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_function_results
  implicit none
  interface
    integer function scope_result(n)
      integer, intent(in) :: n
    end function scope_result
    recursive integer function scope_recur(n) result(answer)
      integer, intent(in) :: n
    end function scope_recur
  end interface
  integer :: scope_result_sentinel, checks
  scope_result_sentinel = -300
  checks = 0
  call expect_equal(scope_result(5), 47, 'function-name result variable')
  call expect_equal(scope_recur(2), 28, 'function-name recursive reference')
  call expect_equal(scope_result_sentinel, -300, 'caller sentinel unchanged')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 FUNCTION RESULTS OK'
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
end program scoping_function_results
integer function scope_result(n)
  implicit none
  integer, intent(in) :: n
  scope_result = -90
  scope_result = 42 + n
end function scope_result
recursive integer function scope_recur(n) result(answer)
  implicit none
  integer, intent(in) :: n
  if (n == 0) then
    answer = 8
  else
    answer = scope_recur(n - 1) + 10
  end if
end function scope_recur
