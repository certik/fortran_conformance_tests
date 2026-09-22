! rule: S11.1.3.3-001
! covers: same-rank-as-selector
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_rank_shape_effect
  implicit none
  integer :: checks
  integer :: grid(-2:4,7:12)
  integer :: dims(2)
  grid=0
  checks=0
  ! Section grid(-1:3:2,8:12:4) is rank two with extents 3 and 2.
  associate (tile => grid(-1:3:2,8:12:4))
    dims=shape(tile)
  if (dims(1) /= 3) then
    write(*,'(a)') 'ACF:rank_shape:rank-two-first-extent'
    error stop
  end if
  checks=checks+1
  if (dims(2) /= 2) then
    write(*,'(a)') 'ACF:rank_shape:rank-two-second-extent'
    error stop
  end if
  checks=checks+1
  end associate
  if (checks /= 2) then
    write(*,'(a)') 'ACF:rank_shape:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE RANK SHAPE OK'
end program associate_construct_rank_shape_effect
