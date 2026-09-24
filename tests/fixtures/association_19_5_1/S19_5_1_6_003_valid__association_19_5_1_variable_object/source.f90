! rule: S19.5.1.6-003
! covers: variable-selector-object-association
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_construct_associate
  implicit none
  integer :: x, checks
  x = 1
  checks = 0
  associate (a => x)
    a = 42
    call expect_equal(x, 42, 'associate-to-selector write')
    x = 77
    call expect_equal(a, 77, 'selector-to-associate write')
  end associate
  call expect_equal(x, 77, 'selector final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 VARIABLE OBJECT OK'
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
end program association_construct_associate
