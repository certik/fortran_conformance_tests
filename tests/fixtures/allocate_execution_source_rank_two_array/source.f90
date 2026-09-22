! rule: S9.7.1.2-010
! covers: array-source-to-same-rank-array
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_source_rank_two_array
  implicit none
  integer :: checks
  integer :: s(2:4,7:8)
  integer, allocatable :: a(:,:)
  integer :: stat
  checks=0
  s(2,7)=127
  s(3,7)=137
  s(4,7)=147
  s(2,8)=128
  s(3,8)=138
  s(4,8)=148
  allocate(a(2:4,7:8), source=s, stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:source_rank_two_array:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:source_rank_two_array:allocated'
    error stop
  end if
  checks=checks+1
  if (any(lbound(a) /= [2,7])) then
    write(*,'(a)') 'AEX:source_rank_two_array:lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(a) /= [4,8])) then
    write(*,'(a)') 'AEX:source_rank_two_array:upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(a) /= [3,2])) then
    write(*,'(a)') 'AEX:source_rank_two_array:shape'
    error stop
  end if
  checks=checks+1
  if (a(2,7) /= 127) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-lower-corner'
    error stop
  end if
  checks=checks+1
  if (a(3,7) /= 137) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-lower-middle'
    error stop
  end if
  checks=checks+1
  if (a(4,7) /= 147) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-lower-upper'
    error stop
  end if
  checks=checks+1
  if (a(2,8) /= 128) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-upper-left'
    error stop
  end if
  checks=checks+1
  if (a(3,8) /= 138) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-middle'
    error stop
  end if
  checks=checks+1
  if (a(4,8) /= 148) then
    write(*,'(a)') 'AEX:source_rank_two_array:value-upper-corner'
    error stop
  end if
  checks=checks+1
  if (checks /= 11) then
    write(*,'(a)') 'AEX:source_rank_two_array:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION SOURCE RANK TWO ARRAY OK'
end program allocate_execution_source_rank_two_array
