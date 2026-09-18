program save_local_return_effect
  implicit none
  integer :: snapshot, entries, exits, returns, local_checks, main_checks
  entries=0
  exits=0
  returns=0
  local_checks=0
  main_checks=0
  snapshot=-1
  call visit(1, 1, 1, snapshot, entries, exits, local_checks)
  returns=returns+1
  if (entries /= 1) then
    write(*,'(a)') 'SLE:return:after-1-entries'
    error stop
  end if
  main_checks=main_checks+1
  if (exits /= 1) then
    write(*,'(a)') 'SLE:return:after-1-exits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'SLE:return:after-1-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (snapshot /= 11) then
    write(*,'(a)') 'SLE:return:after-1-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (local_checks /= 3) then
    write(*,'(a)') 'SLE:return:after-1-local-checks'
    error stop
  end if
  main_checks=main_checks+1
  snapshot=-2
  call visit(2, 2, 2, snapshot, entries, exits, local_checks)
  returns=returns+1
  if (entries /= 2) then
    write(*,'(a)') 'SLE:return:after-2-entries'
    error stop
  end if
  main_checks=main_checks+1
  if (exits /= 2) then
    write(*,'(a)') 'SLE:return:after-2-exits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 2) then
    write(*,'(a)') 'SLE:return:after-2-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (snapshot /= 17) then
    write(*,'(a)') 'SLE:return:after-2-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (local_checks /= 7) then
    write(*,'(a)') 'SLE:return:after-2-local-checks'
    error stop
  end if
  main_checks=main_checks+1
  snapshot=-3
  call visit(3, 3, 3, snapshot, entries, exits, local_checks)
  returns=returns+1
  if (entries /= 3) then
    write(*,'(a)') 'SLE:return:after-3-entries'
    error stop
  end if
  main_checks=main_checks+1
  if (exits /= 3) then
    write(*,'(a)') 'SLE:return:after-3-exits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 3) then
    write(*,'(a)') 'SLE:return:after-3-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (snapshot /= 17) then
    write(*,'(a)') 'SLE:return:after-3-snapshot'
    error stop
  end if
  main_checks=main_checks+1
  if (local_checks /= 11) then
    write(*,'(a)') 'SLE:return:after-3-local-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 15) then
    write(*,'(a)') 'SLE:return:main-check-total'
    error stop
  end if
  write(*,'(a)') 'SAVE LOCAL RETURN OK'
contains
  subroutine visit(phase, expected_phase, expected_entry, snapshot, entries, exits, checks)
    implicit none
    integer, intent(in) :: phase, expected_phase, expected_entry
    integer, intent(out) :: snapshot
    integer, intent(inout) :: entries, exits, checks
    integer :: activation
    integer, save :: kept
    entries=entries+1
    activation=entries
    if (phase /= expected_phase) then
      write(*,'(a,i0)') 'SLE:return:phase:activation=', activation
      error stop
    end if
    checks=checks+1
    if (entries /= expected_entry) then
      write(*,'(a,i0)') 'SLE:return:entry:activation=', activation
      error stop
    end if
    checks=checks+1
    if (phase == 1) then
      kept=11
      if (kept /= 11) then
        write(*,'(a,i0)') 'SLE:return:first-defined:activation=', activation
        error stop
      end if
      checks=checks+1
      snapshot=kept
      exits=exits+1
      return
    else if (phase == 2) then
      if (kept /= 11) then
        write(*,'(a,i0)') 'SLE:return:second-retained:activation=', activation
        error stop
      end if
      checks=checks+1
      kept=17
      if (kept /= 17) then
        write(*,'(a,i0)') 'SLE:return:second-updated:activation=', activation
        error stop
      end if
      checks=checks+1
      snapshot=kept
      exits=exits+1
      return
    else
      if (phase /= 3) then
        write(*,'(a,i0)') 'SLE:return:last-phase:activation=', activation
        error stop
      end if
      checks=checks+1
      if (kept /= 17) then
        write(*,'(a,i0)') 'SLE:return:third-retained:activation=', activation
        error stop
      end if
      checks=checks+1
      snapshot=kept
      exits=exits+1
      return
    end if
    exits=exits+1
  end subroutine visit
end program save_local_return_effect
