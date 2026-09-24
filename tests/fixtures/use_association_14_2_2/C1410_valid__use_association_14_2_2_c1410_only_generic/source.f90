! rule: C1410
! covers: only-use-name-nongeneric-control generic-name-only-item-is-generic-spec
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1410_provider
  implicit none
  integer :: answer = 42
  interface g
    module procedure gi, gr
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
  integer function gr(x)
    real, intent(in) :: x
    gr = 32 + int(x) - int(x)
  end function
end module
program c1410_only_generic
  use c1410_provider, only: answer, g
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (g(3) /= 31 .or. g(2.0) /= 32) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 C1410 ONLY GENERIC OK'
end program
