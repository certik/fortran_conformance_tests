! rule: S14.2.2-009
! covers: ultimate-entity-definition unused-conflicting-identifier-not-prohibited generic-interfaces-merge-across-use
! evidence: effect
! standard: f2023
! oracle-basis: standard
module ultimate_provider
  implicit none
  integer :: shared = 5
end module
module conflict_a
  implicit none
  integer :: x = -1
  integer :: answer_a = 42
end module
module conflict_b
  implicit none
  integer :: x = -2
  integer :: answer_b = 1
end module
module generic_a
  implicit none
  interface g
    module procedure gi
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
end module
module generic_b
  implicit none
  interface g
    module procedure gr
  end interface
contains
  integer function gr(x)
    real, intent(in) :: x
    gr = 32 + int(x) - int(x)
  end function
end module
program ultimate_and_generic
  use ultimate_provider, only: a => shared, b => shared
  use conflict_a, only: x, answer_a
  use conflict_b, only: x, answer_b
  use generic_a
  use generic_b
  implicit none
  integer :: checks
  checks = 0
  a = 42
  if (b /= 42) error stop 1
  checks = checks + 1
  if (answer_a + answer_b /= 43) error stop 2
  checks = checks + 1
  if (g(3) /= 31 .or. g(2.0) /= 32) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ULTIMATE AND GENERIC OK'
end program
