! rule: S9.5.3.3-002
! covers: rank-two-order-value
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_rank_two_effect
  implicit none
  integer :: checks
  integer :: a(-2:1,4:6)
  data a / &
    -1946, &
    -946, &
    54, &
    1054, &
    -1945, &
    -945, &
    55, &
    1055, &
    -1944, &
    -944, &
    56, &
    1056 /
  checks=0
  ! rank 2 formula: j1=-2,j2=4,d1=4; extents 4 and 3 are distinct.
  ! (0,5) position 7: 1+(0-(-2))+(5-4)*4 = 7.
  if (a(0,5) /= 55) then
    write(*,'(a)') 'AEO:rank_two:coordinate-0-5'
    error stop
  end if
  checks=checks+1
  ! (-1,5) position 6: 1+(-1-(-2))+(5-4)*4 = 6.
  if (a(-1,5) /= -945) then
    write(*,'(a)') 'AEO:rank_two:coordinate--1-5'
    error stop
  end if
  checks=checks+1
  ! (1,6) position 12: 1+(1-(-2))+(6-4)*4 = 12.
  if (a(1,6) /= 1056) then
    write(*,'(a)') 'AEO:rank_two:coordinate-1-6'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'AEO:rank_two:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER RANK TWO OK'
end program array_element_order_rank_two_effect
