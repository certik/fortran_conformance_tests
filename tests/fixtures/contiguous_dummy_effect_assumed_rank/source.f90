program contiguous_assumed_rank_effect
  implicit none
  integer :: a(4)
  integer :: entries, updates, exits, checks, main_checks, branches
  a=[11,12,13,14]
  entries=0
  updates=0
  exits=0
  checks=0
  main_checks=0
  branches=0
  if (a(1) /= 11) error stop 'CDE:caller-initial-1'
  main_checks=main_checks+1
  if (a(2) /= 12) error stop 'CDE:caller-initial-2'
  main_checks=main_checks+1
  if (a(3) /= 13) error stop 'CDE:caller-initial-3'
  main_checks=main_checks+1
  if (a(4) /= 14) error stop 'CDE:caller-initial-4'
  main_checks=main_checks+1
  call update_section(a(1:4:2), entries, updates, exits, checks, branches)
  if (entries /= 1) error stop 'CDE:caller-entry'
  main_checks=main_checks+1
  if (updates /= 2) error stop 'CDE:caller-updates'
  main_checks=main_checks+1
  if (exits /= 1) error stop 'CDE:caller-return'
  main_checks=main_checks+1
  if (checks /= 11) error stop 'CDE:caller-procedure-checks'
  main_checks=main_checks+1
  if (branches /= 1) error stop 'CDE:caller-rank-branch'
  main_checks=main_checks+1
  if (a(1) /= 21) error stop 'CDE:caller-returned-1'
  main_checks=main_checks+1
  if (a(2) /= 12) error stop 'CDE:caller-returned-2'
  main_checks=main_checks+1
  if (a(3) /= 23) error stop 'CDE:caller-returned-3'
  main_checks=main_checks+1
  if (a(4) /= 14) error stop 'CDE:caller-returned-4'
  main_checks=main_checks+1
  if (main_checks /= 13) error stop 'CDE:caller-check-total'
  write(*,'(a)') 'CONTIGUOUS ASSUMED RANK OK'
contains
  subroutine update_section(x, entries, updates, exits, checks, branches)
    implicit none
    integer, contiguous, intent(inout) :: x(..)
    integer, intent(inout) :: entries, updates, exits, checks, branches
    entries=entries+1
    if (entries /= 1) error stop 'CDE:dummy-entry'
    checks=checks+1
    if (is_contiguous(x) .neqv. .true.) error stop 'CDE:dummy-contiguity'
    checks=checks+1
    if (rank(x) /= 1) error stop 'CDE:dummy-rank'
    checks=checks+1
    if (size(x) /= 2) error stop 'CDE:dummy-size'
    checks=checks+1
    select rank (r => x)
    rank (1)
      branches=branches+1
      if (branches /= 1) error stop 'CDE:rank-one-branch'
      checks=checks+1
      if (r(1) /= 11) error stop 'CDE:dummy-initial-1'
      checks=checks+1
      if (r(2) /= 13) error stop 'CDE:dummy-initial-2'
      checks=checks+1
      r(1)=r(1)+10
      updates=updates+1
      if (r(1) /= 21) error stop 'CDE:dummy-updated-1'
      checks=checks+1
      r(2)=r(2)+10
      updates=updates+1
      if (r(2) /= 23) error stop 'CDE:dummy-updated-2'
      checks=checks+1
      if (updates /= 2) error stop 'CDE:dummy-update-total'
      checks=checks+1
    rank default
      error stop 'CDE:unexpected-rank'
    end select
    exits=exits+1
    if (exits /= 1) error stop 'CDE:dummy-completed'
    checks=checks+1
  end subroutine update_section
end program contiguous_assumed_rank_effect
