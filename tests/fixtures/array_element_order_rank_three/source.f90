! rule: S9.5.3.3-002
! covers: rank-three-order-value
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_rank_three_effect
  implicit none
  integer :: checks
  integer :: a(-2:0,4:5,7:10)
  data a / &
    80407, &
    90407, &
    100407, &
    80507, &
    90507, &
    100507, &
    80408, &
    90408, &
    100408, &
    80508, &
    90508, &
    100508, &
    80409, &
    90409, &
    100409, &
    80509, &
    90509, &
    100509, &
    80410, &
    90410, &
    100410, &
    80510, &
    90510, &
    100510 /
  checks=0
  ! rank 3: j=(-2,4,7), d1=3, d2=2; s3 advances by d2*d1=6.
  ! (-1,5,9) position 17: 1+(-1-(-2))+(5-4)*3+(9-7)*2*3 = 17.
  if (a(-1,5,9) /= 90509) then
    write(*,'(a)') 'AEO:rank_three:coordinate--1-5-9'
    error stop
  end if
  checks=checks+1
  ! (-2,4,8) position 7: 1+(-2-(-2))+(4-4)*3+(8-7)*2*3 = 7.
  if (a(-2,4,8) /= 80408) then
    write(*,'(a)') 'AEO:rank_three:coordinate--2-4-8'
    error stop
  end if
  checks=checks+1
  ! (0,5,10) position 24: 1+(0-(-2))+(5-4)*3+(10-7)*2*3 = 24.
  if (a(0,5,10) /= 100510) then
    write(*,'(a)') 'AEO:rank_three:coordinate-0-5-10'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'AEO:rank_three:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER RANK THREE OK'
end program array_element_order_rank_three_effect
