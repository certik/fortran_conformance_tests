! rule: S9.7.1.2-001
! covers: default-lower-bound-one
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_default_lower
  implicit none
  integer :: checks
  integer, allocatable :: a(:), b(:)
  integer :: stat
  checks=0
  allocate(a(4), stat=stat)
  allocate(b(-2:1))
  if (stat /= 0) then
    write(*,'(a)') 'AEX:default_lower:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:default_lower:allocated'
    error stop
  end if
  checks=checks+1
  if (lbound(a,1) /= 1) then
    write(*,'(a)') 'AEX:default_lower:a-lower'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= 4) then
    write(*,'(a)') 'AEX:default_lower:a-upper'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 4) then
    write(*,'(a)') 'AEX:default_lower:a-size'
    error stop
  end if
  checks=checks+1
  if (lbound(b,1) /= -2) then
    write(*,'(a)') 'AEX:default_lower:b-lower-control'
    error stop
  end if
  checks=checks+1
  if (ubound(b,1) /= 1) then
    write(*,'(a)') 'AEX:default_lower:b-upper-control'
    error stop
  end if
  checks=checks+1
  a = [41, 42, 43, 44]
  b = [61, 62, 63, 64]
  if (a(1) /= 41) then
    write(*,'(a)') 'AEX:default_lower:a-value-lower'
    error stop
  end if
  checks=checks+1
  if (a(2) /= 42) then
    write(*,'(a)') 'AEX:default_lower:a-value-second'
    error stop
  end if
  checks=checks+1
  if (a(3) /= 43) then
    write(*,'(a)') 'AEX:default_lower:a-value-third'
    error stop
  end if
  checks=checks+1
  if (a(4) /= 44) then
    write(*,'(a)') 'AEX:default_lower:a-value-upper'
    error stop
  end if
  checks=checks+1
  if (b(-2) /= 61) then
    write(*,'(a)') 'AEX:default_lower:b-value-lower'
    error stop
  end if
  checks=checks+1
  if (b(-1) /= 62) then
    write(*,'(a)') 'AEX:default_lower:b-value-second'
    error stop
  end if
  checks=checks+1
  if (b(0) /= 63) then
    write(*,'(a)') 'AEX:default_lower:b-value-third'
    error stop
  end if
  checks=checks+1
  if (b(1) /= 64) then
    write(*,'(a)') 'AEX:default_lower:b-value-upper'
    error stop
  end if
  checks=checks+1
  if (checks /= 15) then
    write(*,'(a)') 'AEX:default_lower:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION DEFAULT LOWER OK'
end program allocate_execution_default_lower
