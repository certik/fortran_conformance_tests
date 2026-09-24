! rule: S14.2.2-004
! covers: use-without-nature-accesses-module nonintrinsic-module-preferred-over-intrinsic
! evidence: effect
! standard: f2023
! oracle-basis: standard
module plain_m
  implicit none
  integer :: answer = 42
end module
module iso_fortran_env
  implicit none
  integer :: collision_answer = 55
end module
program without_nature
  use plain_m, only: answer
  use iso_fortran_env, only: collision_answer
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (collision_answer /= 55) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 WITHOUT NATURE OK'
end program
