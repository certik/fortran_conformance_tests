program save_local_recursive_effect
  implicit none
  integer :: before_snapshot, inner_snapshot, after_snapshot
  integer :: entries, exits, child_returns, returns, local_checks, main_checks
  before_snapshot=-1
  inner_snapshot=-2
  after_snapshot=-3
  entries=0
  exits=0
  child_returns=0
  returns=0
  local_checks=0
  main_checks=0
  call share(0, 0, 1, before_snapshot, inner_snapshot, after_snapshot, &
             entries, exits, child_returns, local_checks)
  returns=returns+1
  if (entries /= 2) then
    write(*,'(a)') 'SLE:recursive:caller-entries'
    error stop
  end if
  main_checks=main_checks+1
  if (exits /= 2) then
    write(*,'(a)') 'SLE:recursive:caller-exits'
    error stop
  end if
  main_checks=main_checks+1
  if (child_returns /= 1) then
    write(*,'(a)') 'SLE:recursive:caller-child-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'SLE:recursive:caller-outer-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (before_snapshot /= 11) then
    write(*,'(a)') 'SLE:recursive:caller-before-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (inner_snapshot /= 11) then
    write(*,'(a)') 'SLE:recursive:caller-inner-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (after_snapshot /= 17) then
    write(*,'(a)') 'SLE:recursive:caller-after-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (local_checks /= 12) then
    write(*,'(a)') 'SLE:recursive:caller-local-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 8) then
    write(*,'(a)') 'SLE:recursive:main-check-total'
    error stop
  end if
  write(*,'(a)') 'SAVE LOCAL RECURSIVE OK'
contains
  recursive subroutine share(depth, expected_depth, expected_entry, before_snapshot, &
                             inner_snapshot, after_snapshot, entries, exits, child_returns, checks)
    implicit none
    integer, intent(in) :: depth, expected_depth, expected_entry
    integer, intent(inout) :: before_snapshot, inner_snapshot, after_snapshot
    integer, intent(inout) :: entries, exits, child_returns, checks
    integer :: activation
    integer, save :: kept
    entries=entries+1
    activation=entries
    if (depth /= expected_depth) then
      write(*,'(a,i0)') 'SLE:recursive:depth:activation=', activation
      error stop
    end if
    checks=checks+1
    if (entries /= expected_entry) then
      write(*,'(a,i0)') 'SLE:recursive:entry:activation=', activation
      error stop
    end if
    checks=checks+1
    if (depth == 0) then
      kept=11
      if (kept /= 11) then
        write(*,'(a,i0)') 'SLE:recursive:outer-defined:activation=', activation
        error stop
      end if
      checks=checks+1
      before_snapshot=kept
      call share(1, 1, 2, before_snapshot, inner_snapshot, after_snapshot, &
                 entries, exits, child_returns, checks)
      child_returns=child_returns+1
      if (child_returns /= 1) then
        write(*,'(a,i0)') 'SLE:recursive:inner-return:activation=', activation
        error stop
      end if
      checks=checks+1
      if (entries /= 2) then
        write(*,'(a,i0)') 'SLE:recursive:outer-resumed-entries:activation=', activation
        error stop
      end if
      checks=checks+1
      if (exits /= 1) then
        write(*,'(a,i0)') 'SLE:recursive:inner-exit:activation=', activation
        error stop
      end if
      checks=checks+1
      if (kept /= 17) then
        write(*,'(a,i0)') 'SLE:recursive:outer-shared:activation=', activation
        error stop
      end if
      checks=checks+1
      after_snapshot=kept
      exits=exits+1
      return
    else
      if (depth /= 1) then
        write(*,'(a,i0)') 'SLE:recursive:inner-depth:activation=', activation
        error stop
      end if
      checks=checks+1
      if (kept /= 11) then
        write(*,'(a,i0)') 'SLE:recursive:inner-shared:activation=', activation
        error stop
      end if
      checks=checks+1
      inner_snapshot=kept
      kept=17
      if (kept /= 17) then
        write(*,'(a,i0)') 'SLE:recursive:inner-updated:activation=', activation
        error stop
      end if
      checks=checks+1
      exits=exits+1
      return
    end if
    exits=exits+1
  end subroutine share
end program save_local_recursive_effect
