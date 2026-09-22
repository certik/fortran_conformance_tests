! rule: S9.7.1.2-010
! covers: scalar-source-broadcast-to-array
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_source_scalar_broadcast
  implicit none
  integer :: checks
  integer, allocatable :: a(:)
  integer :: stat
  checks=0
  allocate(a(-2:2), source=7, stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:allocated'
    error stop
  end if
  checks=checks+1
  if (lbound(a,1) /= -2) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:lower'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= 2) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:upper'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 5) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:size'
    error stop
  end if
  checks=checks+1
  if (a(-2) /= 7) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:value--2'
    error stop
  end if
  checks=checks+1
  if (a(-1) /= 7) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:value--1'
    error stop
  end if
  checks=checks+1
  if (a(0) /= 7) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:value-0'
    error stop
  end if
  checks=checks+1
  if (a(1) /= 7) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:value-1'
    error stop
  end if
  checks=checks+1
  if (a(2) /= 7) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:value-2'
    error stop
  end if
  checks=checks+1
  if (checks /= 10) then
    write(*,'(a)') 'AEX:source_scalar_broadcast:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION SOURCE SCALAR BROADCAST OK'
end program allocate_execution_source_scalar_broadcast
