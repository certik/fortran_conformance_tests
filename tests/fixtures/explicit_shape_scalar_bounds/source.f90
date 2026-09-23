! rule: S8.5.8.2-002
! covers: upper-only-default,per-dimension-bounds,mixed-omitted-lowers
! Expected bounds, extents and payloads are hand-derived from Fortran 2023 8.5.8.2.
program explicit_shape_scalar_bounds
  implicit none
  integer :: checks
  integer :: upper_only(4)
  integer :: explicit2d(-2:0,4:5)
  integer :: mixed(2,-1:1)
  checks=0
  upper_only=41
  explicit2d=52
  mixed=63
  if (rank(upper_only) /= 1) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-rank'
    error stop
  end if
  checks=checks+1
  if (any(lbound(upper_only) /= [1])) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(upper_only) /= [4])) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(upper_only) /= [4])) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-shape'
    error stop
  end if
  checks=checks+1
  if (size(upper_only) /= 4) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-size'
    error stop
  end if
  checks=checks+1
  if (count(upper_only == 41) /= 4) then
    write(*,'(a)') 'ESH:scalar_bounds:upper-only-values'
    error stop
  end if
  checks=checks+1
  if (rank(explicit2d) /= 2) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-rank'
    error stop
  end if
  checks=checks+1
  if (any(lbound(explicit2d) /= [-2,4])) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(explicit2d) /= [0,5])) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(explicit2d) /= [3,2])) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-shape'
    error stop
  end if
  checks=checks+1
  if (size(explicit2d) /= 6) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-size'
    error stop
  end if
  checks=checks+1
  if (count(explicit2d == 52) /= 6) then
    write(*,'(a)') 'ESH:scalar_bounds:explicit2d-values'
    error stop
  end if
  checks=checks+1
  if (rank(mixed) /= 2) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-rank'
    error stop
  end if
  checks=checks+1
  if (any(lbound(mixed) /= [1,-1])) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(mixed) /= [2,1])) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(mixed) /= [2,3])) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-shape'
    error stop
  end if
  checks=checks+1
  if (size(mixed) /= 6) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-size'
    error stop
  end if
  checks=checks+1
  if (count(mixed == 63) /= 6) then
    write(*,'(a)') 'ESH:scalar_bounds:mixed-values'
    error stop
  end if
  checks=checks+1
  if (checks /= 18) then
    write(*,'(a)') 'ESH:scalar_bounds:check-total'
    error stop
  end if
  write(*,'(a)') 'EXPLICIT SHAPE SCALAR BOUNDS OK'
end program explicit_shape_scalar_bounds
