! rule: R1409
! covers: use-stmt-rename-list-form use-stmt-only-list-form use-stmt-module-nature-form
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1409_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 5
  integer :: noise = -999
end module
program use_stmt_forms
  use, non_intrinsic :: r1409_provider, only: nature_answer => answer
  use r1409_provider, rename_bonus => bonus
  use r1409_provider, only: only_answer => answer
  implicit none
  integer :: checks
  checks = 0
  if (rename_bonus /= 5) error stop 1
  checks = checks + 1
  if (only_answer /= 42) error stop 2
  checks = checks + 1
  if (nature_answer /= 42) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 USE STMT FORMS OK'
end program
