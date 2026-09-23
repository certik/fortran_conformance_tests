! rule: S8.5.8.2-004
! covers: empty-one-dimensional,mixed-zero-extent
! Expected bounds, extents and payloads are hand-derived from Fortran 2023 8.5.8.2.
program explicit_shape_empty_ranges
  implicit none
  integer :: checks
  integer :: empty1(5:3)
  integer :: empty2(5:3,-2:1)
  integer :: reached
  checks=0
  reached=917
  if (rank(empty1) /= 1) then
    write(*,'(a)') 'ESH:empty_ranges:empty1-rank'
    error stop
  end if
  checks=checks+1
  if (any(lbound(empty1) /= [1])) then
    write(*,'(a)') 'ESH:empty_ranges:empty1-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(empty1) /= [0])) then
    write(*,'(a)') 'ESH:empty_ranges:empty1-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(empty1) /= [0])) then
    write(*,'(a)') 'ESH:empty_ranges:empty1-shape'
    error stop
  end if
  checks=checks+1
  if (size(empty1) /= 0) then
    write(*,'(a)') 'ESH:empty_ranges:empty1-size'
    error stop
  end if
  checks=checks+1
  if (rank(empty2) /= 2) then
    write(*,'(a)') 'ESH:empty_ranges:empty2-rank'
    error stop
  end if
  checks=checks+1
  if (any(lbound(empty2) /= [1,-2])) then
    write(*,'(a)') 'ESH:empty_ranges:empty2-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(empty2) /= [0,1])) then
    write(*,'(a)') 'ESH:empty_ranges:empty2-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(empty2) /= [0,4])) then
    write(*,'(a)') 'ESH:empty_ranges:empty2-shape'
    error stop
  end if
  checks=checks+1
  if (size(empty2) /= 0) then
    write(*,'(a)') 'ESH:empty_ranges:empty2-size'
    error stop
  end if
  checks=checks+1
  if (reached /= 917) then
    write(*,'(a)') 'ESH:empty_ranges:path-sentinel'
    error stop
  end if
  checks=checks+1
  if (checks /= 11) then
    write(*,'(a)') 'ESH:empty_ranges:check-total'
    error stop
  end if
  write(*,'(a)') 'EXPLICIT SHAPE EMPTY RANGES OK'
end program explicit_shape_empty_ranges
