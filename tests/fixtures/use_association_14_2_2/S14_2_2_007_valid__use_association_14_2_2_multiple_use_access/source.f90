! rule: S14.2.2-007
! covers: one-non-only-use-makes-all-public-accessible all-only-uses-union-only-lists
! evidence: effect
! standard: f2023
! oracle-basis: standard
module multi_use_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 1
  integer :: noise = -999
end module
module multi_wrong_provider
  implicit none
  integer :: noise = -7
end module
program multiple_use_access
  implicit none
  integer :: checks
  checks = 0
  call check_non_only(checks)
  call check_all_only_union(checks)
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MULTIPLE USE ACCESS OK'
contains
  subroutine check_non_only(checks)
    use multi_use_provider, only: answer
    use multi_use_provider
    implicit none
    integer, intent(inout) :: checks
    if (answer + bonus + noise /= -956) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_all_only_union(checks)
    use multi_use_provider, only: answer
    use multi_use_provider, only: bonus
    use multi_wrong_provider, only: noise
    implicit none
    integer, intent(inout) :: checks
    if (answer + bonus + noise /= 36) error stop 2
    checks = checks + 1
  end subroutine
end program
