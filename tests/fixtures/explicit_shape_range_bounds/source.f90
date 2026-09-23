! rule: S8.5.8.2-004
! covers: bound-signs,inclusive-nonempty-range,singleton-zero-bound
! Expected bounds, extents and payloads are hand-derived from Fortran 2023 8.5.8.2.
program explicit_shape_range_bounds
  implicit none
  integer :: checks
  integer :: positive_range(2:4)
  integer :: negative_range(-2:0)
  integer :: zero_singleton(0:0)
  checks=0
  positive_range=68
  negative_range=74
  zero_singleton=85
  if (any(lbound(positive_range) /= [2])) then
    write(*,'(a)') 'ESH:range_bounds:positive-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(positive_range) /= [4])) then
    write(*,'(a)') 'ESH:range_bounds:positive-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(positive_range) /= [3])) then
    write(*,'(a)') 'ESH:range_bounds:positive-shape'
    error stop
  end if
  checks=checks+1
  if (size(positive_range) /= 3) then
    write(*,'(a)') 'ESH:range_bounds:positive-size'
    error stop
  end if
  checks=checks+1
  if (positive_range(lbound(positive_range,1)) /= 68) then
    write(*,'(a)') 'ESH:range_bounds:positive-lower-endpoint'
    error stop
  end if
  checks=checks+1
  if (positive_range(ubound(positive_range,1)) /= 68) then
    write(*,'(a)') 'ESH:range_bounds:positive-upper-endpoint'
    error stop
  end if
  checks=checks+1
  if (any(lbound(negative_range) /= [-2])) then
    write(*,'(a)') 'ESH:range_bounds:negative-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(negative_range) /= [0])) then
    write(*,'(a)') 'ESH:range_bounds:negative-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(negative_range) /= [3])) then
    write(*,'(a)') 'ESH:range_bounds:negative-shape'
    error stop
  end if
  checks=checks+1
  if (size(negative_range) /= 3) then
    write(*,'(a)') 'ESH:range_bounds:negative-size'
    error stop
  end if
  checks=checks+1
  if (negative_range(lbound(negative_range,1)) /= 74) then
    write(*,'(a)') 'ESH:range_bounds:negative-lower-endpoint'
    error stop
  end if
  checks=checks+1
  if (negative_range(ubound(negative_range,1)) /= 74) then
    write(*,'(a)') 'ESH:range_bounds:negative-upper-endpoint'
    error stop
  end if
  checks=checks+1
  if (any(lbound(zero_singleton) /= [0])) then
    write(*,'(a)') 'ESH:range_bounds:zero-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(zero_singleton) /= [0])) then
    write(*,'(a)') 'ESH:range_bounds:zero-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(zero_singleton) /= [1])) then
    write(*,'(a)') 'ESH:range_bounds:zero-shape'
    error stop
  end if
  checks=checks+1
  if (size(zero_singleton) /= 1) then
    write(*,'(a)') 'ESH:range_bounds:zero-size'
    error stop
  end if
  checks=checks+1
  if (zero_singleton(lbound(zero_singleton,1)) /= 85) then
    write(*,'(a)') 'ESH:range_bounds:zero-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 17) then
    write(*,'(a)') 'ESH:range_bounds:check-total'
    error stop
  end if
  write(*,'(a)') 'EXPLICIT SHAPE RANGE BOUNDS OK'
end program explicit_shape_range_bounds
