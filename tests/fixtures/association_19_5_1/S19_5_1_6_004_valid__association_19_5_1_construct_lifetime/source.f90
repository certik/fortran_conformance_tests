! rule: S19.5.1.6-004
! covers:
!   associate-name-remains-associated-through-block
!   selector-accessed-by-associate-name
!   construct-association-terminates-on-completion
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_construct_lifetime
  implicit none
  integer :: x, a, observed, checks
  x = 1
  a = -777
  observed = -11
  checks = 0
  associate (a => x)
    call expect_equal(a, 1, 'associate name accesses selector')
    a = 42
    if (x == 42) then
      do observed = 1, 2
        a = a + observed
      end do
    end if
    call expect_equal(a, 45, 'associate name remains through block')
  end associate
  a = 99
  call expect_equal(x, 45, 'selector keeps associated write after construct')
  call expect_equal(a, 99, 'outer name restored after construct')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT LIFETIME OK'
contains
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_lifetime
