! rule: S9.7.1.2-010
! covers: ordinary-source-value-same-rank
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_source_same_rank_vector
  implicit none
  integer :: checks
  integer, allocatable :: a(:)
  integer :: stat
  checks=0
  allocate(a(-4:-2), source=[11,22,33], stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:source_same_rank_vector:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:source_same_rank_vector:allocated'
    error stop
  end if
  checks=checks+1
  if (lbound(a,1) /= -4) then
    write(*,'(a)') 'AEX:source_same_rank_vector:lower'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= -2) then
    write(*,'(a)') 'AEX:source_same_rank_vector:upper'
    error stop
  end if
  checks=checks+1
  if (size(a) /= 3) then
    write(*,'(a)') 'AEX:source_same_rank_vector:size'
    error stop
  end if
  checks=checks+1
  if (a(-4) /= 11) then
    write(*,'(a)') 'AEX:source_same_rank_vector:value-first'
    error stop
  end if
  checks=checks+1
  if (a(-3) /= 22) then
    write(*,'(a)') 'AEX:source_same_rank_vector:value-second'
    error stop
  end if
  checks=checks+1
  if (a(-2) /= 33) then
    write(*,'(a)') 'AEX:source_same_rank_vector:value-third'
    error stop
  end if
  checks=checks+1
  if (checks /= 8) then
    write(*,'(a)') 'AEX:source_same_rank_vector:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION SOURCE SAME RANK VECTOR OK'
end program allocate_execution_source_same_rank_vector
