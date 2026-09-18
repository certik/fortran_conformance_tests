program contiguous_assumed_shape_effect
  implicit none
  integer :: a(4)
  integer :: entries, updates, exits, checks, main_checks
  a=[11,12,13,14]
  entries=0
  updates=0
  exits=0
  checks=0
  main_checks=0
  if (a(1) /= 11) error stop 'CDE:caller-initial-1'
  main_checks=main_checks+1
  if (a(2) /= 12) error stop 'CDE:caller-initial-2'
  main_checks=main_checks+1
  if (a(3) /= 13) error stop 'CDE:caller-initial-3'
  main_checks=main_checks+1
  if (a(4) /= 14) error stop 'CDE:caller-initial-4'
  main_checks=main_checks+1
  call update_section(a(1:4:2), entries, updates, exits, checks)
  if (entries /= 1) error stop 'CDE:caller-entry'
  main_checks=main_checks+1
  if (updates /= 2) error stop 'CDE:caller-updates'
  main_checks=main_checks+1
  if (exits /= 1) error stop 'CDE:caller-return'
  main_checks=main_checks+1
  if (checks /= 10) error stop 'CDE:caller-procedure-checks'
  main_checks=main_checks+1
  if (a(1) /= 21) error stop 'CDE:caller-returned-1'
  main_checks=main_checks+1
  if (a(2) /= 12) error stop 'CDE:caller-returned-2'
  main_checks=main_checks+1
  if (a(3) /= 23) error stop 'CDE:caller-returned-3'
  main_checks=main_checks+1
  if (a(4) /= 14) error stop 'CDE:caller-returned-4'
  main_checks=main_checks+1
  if (main_checks /= 12) error stop 'CDE:caller-check-total'
  write(*,'(a)') 'CONTIGUOUS ASSUMED SHAPE OK'
contains
  subroutine update_section(x, entries, updates, exits, checks)
    implicit none
    integer, contiguous, intent(inout) :: x(:)
    integer, intent(inout) :: entries, updates, exits, checks
    entries=entries+1
    if (entries /= 1) error stop 'CDE:dummy-entry'
    checks=checks+1
    if (is_contiguous(x) .neqv. .true.) error stop 'CDE:dummy-contiguity'
    checks=checks+1
    if (rank(x) /= 1) error stop 'CDE:dummy-rank'
    checks=checks+1
    if (size(x) /= 2) error stop 'CDE:dummy-size'
    checks=checks+1
    if (x(1) /= 11) error stop 'CDE:dummy-initial-1'
    checks=checks+1
    if (x(2) /= 13) error stop 'CDE:dummy-initial-2'
    checks=checks+1
    x(1)=x(1)+10
    updates=updates+1
    if (x(1) /= 21) error stop 'CDE:dummy-updated-1'
    checks=checks+1
    x(2)=x(2)+10
    updates=updates+1
    if (x(2) /= 23) error stop 'CDE:dummy-updated-2'
    checks=checks+1
    if (updates /= 2) error stop 'CDE:dummy-update-total'
    checks=checks+1
    exits=exits+1
    if (exits /= 1) error stop 'CDE:dummy-completed'
    checks=checks+1
  end subroutine update_section
end program contiguous_assumed_shape_effect
