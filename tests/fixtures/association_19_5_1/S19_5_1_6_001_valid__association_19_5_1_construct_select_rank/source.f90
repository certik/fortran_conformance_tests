! rule: S19.5.1.6-001
! covers: select-rank-establishes-selector-association
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_construct_select_rank
  implicit none
  integer :: x(2), checks
  x = [1, 2]
  checks = 0
  call inner(x)
  call expect_equal(x(2), 77, 'select rank final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT SELECT RANK OK'
contains
  subroutine inner(selector)
    implicit none
    integer, intent(inout) :: selector(..)
    select rank (a => selector)
    rank (1)
      a(2) = 42
      call expect_equal(x(2), 42, 'select rank associate-to-selector')
      x(2) = 77
      call expect_equal(a(2), 77, 'select rank selector-to-associate')
    rank default
      error stop 'wrong rank'
    end select
  end subroutine inner
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
end program association_construct_select_rank
