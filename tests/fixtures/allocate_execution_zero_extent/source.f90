! rule: S9.7.1.2-001
! covers: zero-extent-single-dimension,zero-sized-array-defined-status-boundary
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_zero_extent
  implicit none
  integer :: checks
  integer, allocatable :: a(:)
  integer :: stat, reached
  checks=0
  reached=917
  allocate(a(5:3), stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:zero_extent:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:zero_extent:allocated'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 0) then
    write(*,'(a)') 'AEX:zero_extent:size-zero'
    error stop
  end if
  checks=checks+1
  if (reached /= 917) then
    write(*,'(a)') 'AEX:zero_extent:path-sentinel'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'AEX:zero_extent:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION ZERO EXTENT OK'
end program allocate_execution_zero_extent
