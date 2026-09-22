! rule: S9.7.1.2-001
! covers: explicit-lower-and-upper-bounds
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_explicit_bounds
  implicit none
  integer :: checks
  integer, allocatable :: a(:)
  integer :: stat
  checks=0
  allocate(a(3:5), stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:explicit_bounds:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:explicit_bounds:allocated'
    error stop
  end if
  checks=checks+1
  if (lbound(a,1) /= 3) then
    write(*,'(a)') 'AEX:explicit_bounds:lower'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= 5) then
    write(*,'(a)') 'AEX:explicit_bounds:upper'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 3) then
    write(*,'(a)') 'AEX:explicit_bounds:size'
    error stop
  end if
  checks=checks+1
  a = [31, 32, 33]
  if (a(3) /= 31) then
    write(*,'(a)') 'AEX:explicit_bounds:value-lower'
    error stop
  end if
  checks=checks+1
  if (a(4) /= 32) then
    write(*,'(a)') 'AEX:explicit_bounds:value-middle'
    error stop
  end if
  checks=checks+1
  if (a(5) /= 33) then
    write(*,'(a)') 'AEX:explicit_bounds:value-upper'
    error stop
  end if
  checks=checks+1
  if (checks /= 8) then
    write(*,'(a)') 'AEX:explicit_bounds:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION EXPLICIT BOUNDS OK'
end program allocate_execution_explicit_bounds
