! rule: S19.3.1-001
! covers: per-procedure-argument-keyword-local-identifiers
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_argument_keyword_mod
  implicit none
contains
  integer function first_proc(item, other)
    integer, intent(in) :: item, other
    first_proc = item * 10 + other
  end function first_proc
  integer function second_proc(item, other)
    integer, intent(in) :: item, other
    second_proc = item * 100 + other
  end function second_proc
end module scoping_argument_keyword_mod
program scoping_argument_keywords
  use scoping_argument_keyword_mod, only: first_proc, second_proc
  implicit none
  integer :: checks
  checks = 0
  call expect_equal(first_proc(other=7, item=3), 37, 'first procedure keyword class')
  call expect_equal(second_proc(other=8, item=4), 408, 'second procedure keyword class')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 ARGUMENT KEYWORDS OK'
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
end program scoping_argument_keywords
