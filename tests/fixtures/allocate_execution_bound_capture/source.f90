! rule: S9.7.1.2-001
! covers: bounds-captured-after-expression-change
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_bound_capture
  implicit none
  integer :: checks
  integer, allocatable :: a(:)
  integer :: lo, hi, stat
  checks=0
  lo = 2
  hi = 4
  allocate(a(lo:hi), stat=stat)
  lo = -5
  hi = 9
  if (stat /= 0) then
    write(*,'(a)') 'AEX:bound_capture:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:bound_capture:allocated'
    error stop
  end if
  checks=checks+1
  if (lbound(a,1) /= 2) then
    write(*,'(a)') 'AEX:bound_capture:lower-captured'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= 4) then
    write(*,'(a)') 'AEX:bound_capture:upper-captured'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 3) then
    write(*,'(a)') 'AEX:bound_capture:size-captured'
    error stop
  end if
  checks=checks+1
  a = [52, 53, 54]
  if (a(2) /= 52) then
    write(*,'(a)') 'AEX:bound_capture:value-lower'
    error stop
  end if
  checks=checks+1
  if (a(3) /= 53) then
    write(*,'(a)') 'AEX:bound_capture:value-middle'
    error stop
  end if
  checks=checks+1
  if (a(4) /= 54) then
    write(*,'(a)') 'AEX:bound_capture:value-upper'
    error stop
  end if
  checks=checks+1
  if (lo /= -5) then
    write(*,'(a)') 'AEX:bound_capture:changed-lo'
    error stop
  end if
  checks=checks+1
  if (hi /= 9) then
    write(*,'(a)') 'AEX:bound_capture:changed-hi'
    error stop
  end if
  checks=checks+1
  if (checks /= 10) then
    write(*,'(a)') 'AEX:bound_capture:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION BOUND CAPTURE OK'
end program allocate_execution_bound_capture
