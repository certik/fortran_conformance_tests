! rule: S15.5.2.3-002
! covers: chosen-variable-actual
! evidence: effect
! standard: f2023
program conditional_argument_selection
  implicit none
  integer :: checks = 0
  integer :: got = -99, variable_actual = 57
  call take((.true. ? 101 : 202), got)
  call expect_equal(got, 101, 'first true consequent')
  call take((.false. ? 11 : 33), got)
  call expect_equal(got, 33, 'last consequent default')
  call take((.true. ? variable_actual : 58), got)
  call expect_equal(got, 57, 'chosen variable actual')
  call expect_equal(checks, 3, 'check count')
  write(*,'(a)') 'CONDITIONAL ARGUMENT SELECTION OK'
contains
  subroutine take(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
