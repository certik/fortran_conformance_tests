program explicit_procedure_bounds
  implicit none
  integer :: n, entries, changes, undefined_events, checks, returns, main_checks
  entries=0
  changes=0
  undefined_events=0
  checks=0
  returns=0
  main_checks=0
  n=3
  call capture(n, 1, 3, 6, 101, entries, changes, undefined_events, checks)
  returns=returns+1
  if (n /= 3) error stop 'EBC:caller-1-restored'
  main_checks=main_checks+1
  if (entries /= 1) error stop 'EBC:caller-1-entries'
  main_checks=main_checks+1
  if (changes /= 1) error stop 'EBC:caller-1-changes'
  main_checks=main_checks+1
  if (undefined_events /= 1) error stop 'EBC:caller-1-undefined-events'
  main_checks=main_checks+1
  if (returns /= 1) error stop 'EBC:caller-1-returns'
  main_checks=main_checks+1
  if (checks /= 20) error stop 'EBC:caller-1-procedure-checks'
  main_checks=main_checks+1
  n=1
  call capture(n, 2, 1, 4, 102, entries, changes, undefined_events, checks)
  returns=returns+1
  if (n /= 1) error stop 'EBC:caller-2-restored'
  main_checks=main_checks+1
  if (entries /= 2) error stop 'EBC:caller-2-entries'
  main_checks=main_checks+1
  if (changes /= 2) error stop 'EBC:caller-2-changes'
  main_checks=main_checks+1
  if (undefined_events /= 2) error stop 'EBC:caller-2-undefined-events'
  main_checks=main_checks+1
  if (returns /= 2) error stop 'EBC:caller-2-returns'
  main_checks=main_checks+1
  if (checks /= 40) error stop 'EBC:caller-2-procedure-checks'
  main_checks=main_checks+1
  if (main_checks /= 12) error stop 'EBC:caller-check-total'
  write(*,'(a)') 'EXPLICIT PROCEDURE BOUNDS OK'
contains
  subroutine capture(n, visit, upper_expected, extent_expected, value_expected, &
                     entries, changes, undefined_events, checks)
    integer, intent(inout) :: n, entries, changes, undefined_events, checks
    integer, intent(in) :: visit, upper_expected, extent_expected, value_expected
    integer :: a(-2:n)
    a=100+visit
    entries=entries+1
    if (entries /= visit) then
      write(*,'(a,i1)') 'EBC:procedure-entry:activation=', visit
      error stop 'EBC:procedure-entry'
    end if
    checks=checks+1
    if (lbound(a,1) /= -2) then
      write(*,'(a,i1)') 'EBC:procedure-initial-lower:activation=', visit
      error stop 'EBC:procedure-initial-lower'
    end if
    checks=checks+1
    if (ubound(a,1) /= upper_expected) then
      write(*,'(a,i1)') 'EBC:procedure-initial-upper:activation=', visit
      error stop 'EBC:procedure-initial-upper'
    end if
    checks=checks+1
    if (size(a) /= extent_expected) then
      write(*,'(a,i1)') 'EBC:procedure-initial-size:activation=', visit
      error stop 'EBC:procedure-initial-size'
    end if
    checks=checks+1
    if (any(shape(a) /= [extent_expected])) then
      write(*,'(a,i1)') 'EBC:procedure-initial-shape:activation=', visit
      error stop 'EBC:procedure-initial-shape'
    end if
    checks=checks+1
    if (any(a /= value_expected)) then
      write(*,'(a,i1)') 'EBC:procedure-initial-values:activation=', visit
      error stop 'EBC:procedure-initial-values'
    end if
    checks=checks+1
    n=0
    changes=changes+1
    if (changes /= visit) then
      write(*,'(a,i1)') 'EBC:procedure-change:activation=', visit
      error stop 'EBC:procedure-change'
    end if
    checks=checks+1
    if (n /= 0) then
      write(*,'(a,i1)') 'EBC:procedure-source-zero:activation=', visit
      error stop 'EBC:procedure-source-zero'
    end if
    checks=checks+1
    if (lbound(a,1) /= -2) then
      write(*,'(a,i1)') 'EBC:procedure-redefined-lower:activation=', visit
      error stop 'EBC:procedure-redefined-lower'
    end if
    checks=checks+1
    if (ubound(a,1) /= upper_expected) then
      write(*,'(a,i1)') 'EBC:procedure-redefined-upper:activation=', visit
      error stop 'EBC:procedure-redefined-upper'
    end if
    checks=checks+1
    if (size(a) /= extent_expected) then
      write(*,'(a,i1)') 'EBC:procedure-redefined-size:activation=', visit
      error stop 'EBC:procedure-redefined-size'
    end if
    checks=checks+1
    if (any(shape(a) /= [extent_expected])) then
      write(*,'(a,i1)') 'EBC:procedure-redefined-shape:activation=', visit
      error stop 'EBC:procedure-redefined-shape'
    end if
    checks=checks+1
    if (any(a /= value_expected)) then
      write(*,'(a,i1)') 'EBC:procedure-redefined-values:activation=', visit
      error stop 'EBC:procedure-redefined-values'
    end if
    checks=checks+1
    call make_undefined(n, undefined_events)
    if (undefined_events /= visit) then
      write(*,'(a,i1)') 'EBC:procedure-undefinition-event:activation=', visit
      error stop 'EBC:procedure-undefinition-event'
    end if
    checks=checks+1
    if (lbound(a,1) /= -2) then
      write(*,'(a,i1)') 'EBC:procedure-undefined-source-lower:activation=', visit
      error stop 'EBC:procedure-undefined-source-lower'
    end if
    checks=checks+1
    if (ubound(a,1) /= upper_expected) then
      write(*,'(a,i1)') 'EBC:procedure-undefined-source-upper:activation=', visit
      error stop 'EBC:procedure-undefined-source-upper'
    end if
    checks=checks+1
    if (size(a) /= extent_expected) then
      write(*,'(a,i1)') 'EBC:procedure-undefined-source-size:activation=', visit
      error stop 'EBC:procedure-undefined-source-size'
    end if
    checks=checks+1
    if (any(shape(a) /= [extent_expected])) then
      write(*,'(a,i1)') 'EBC:procedure-undefined-source-shape:activation=', visit
      error stop 'EBC:procedure-undefined-source-shape'
    end if
    checks=checks+1
    if (any(a /= value_expected)) then
      write(*,'(a,i1)') 'EBC:procedure-undefined-source-values:activation=', visit
      error stop 'EBC:procedure-undefined-source-values'
    end if
    checks=checks+1
    n=upper_expected
    if (n /= upper_expected) then
      write(*,'(a,i1)') 'EBC:procedure-restored:activation=', visit
      error stop 'EBC:procedure-restored'
    end if
    checks=checks+1
  end subroutine capture
  subroutine make_undefined(value, event_count)
    integer, intent(out) :: value
    integer, intent(inout) :: event_count
    event_count=event_count+1
  end subroutine make_undefined
end program explicit_procedure_bounds
