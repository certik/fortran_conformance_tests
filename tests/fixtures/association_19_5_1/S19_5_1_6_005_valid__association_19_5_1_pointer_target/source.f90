! rule: S19.5.1.6-005
! covers: pointer-associate-name-target
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_pointer_target
  implicit none
  integer, target :: t
  integer, pointer :: p
  integer :: checks
  t = 1
  p => t
  checks = 0
  associate (a => p)
    a = 42
    call expect_equal(t, 42, 'pointer associate writes target')
    t = 77
    call expect_equal(a, 77, 'target write visible through associate')
  end associate
  call expect_equal(t, 77, 'target final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 POINTER TARGET OK'
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
end program association_pointer_target
