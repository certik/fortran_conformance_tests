! rule: S11.1.3.3-001
! covers: upper-bound-from-extent
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_upper_bound_extent_effect
  implicit none
  integer :: checks
  integer :: base(10:21)
  integer :: lo, hi, extent
  base=0
  checks=0
  ! Section base(12:20:3) selects 12,15,18: LBOUND 1, extent 3, UBOUND 3.
  associate (vec => base(12:20:3))
    lo=lbound(vec,1)
    hi=ubound(vec,1)
    extent=size(vec)
  end associate
  if (lo /= 1) then
    write(*,'(a)') 'ACF:upper_bound_extent:section-lower-one'
    error stop
  end if
  checks=checks+1
  if (extent /= 3) then
    write(*,'(a)') 'ACF:upper_bound_extent:section-extent-three'
    error stop
  end if
  checks=checks+1
  if (hi /= 3) then
    write(*,'(a)') 'ACF:upper_bound_extent:upper-from-extent'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'ACF:upper_bound_extent:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE UPPER BOUND EXTENT OK'
end program associate_construct_upper_bound_extent_effect
