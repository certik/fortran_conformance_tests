! rule: S9.5.3.3-002
! covers: rank-fifteen-pattern
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_rank_fifteen_effect
  implicit none
  integer :: checks
  character(len=40) :: a(3:4,-2:-1,5:6, &
       8:8,9:9,10:10,11:11,12:12,13:13,14:14, &
       15:15,16:16,17:17,18:18,-5:-4)
  data a / &
    '3,-2,5,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '4,-2,5,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '3,-1,5,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '4,-1,5,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '3,-2,6,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '4,-2,6,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '3,-1,6,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-5', &
    '3,-2,5,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '4,-2,5,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '3,-1,5,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '4,-1,5,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '3,-2,6,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '4,-2,6,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '3,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4', &
    '4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4' /
  checks=0
  ! rank 15: d1=d2=d3=d15=2 and d4..d14=1; all lower bounds are nonunit.
  ! (4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4) has Table 9.1 position 16.
  ! Arithmetic: 1+(4-(3))+(-1-(-2))*2+(6-(5))*4+(-4-(-5))*8 = 16; dimensions 4:14 have zero deltas.
  if (a(4,-1,6,8,9,10,11,12,13,14, &
       15,16,17,18,-4) /= '4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4') then
    write(*,'(a)') 'AEO:rank_fifteen:coordinate-16'
    error stop
  end if
  checks=checks+1
  ! (4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-5) has Table 9.1 position 8.
  ! Arithmetic: 1+(4-(3))+(-1-(-2))*2+(6-(5))*4 = 8; dimensions 4:14 have zero deltas.
  if (a(4,-1,6,8,9,10,11,12,13,14, &
       15,16,17,18,-5) /= '4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-5') then
    write(*,'(a)') 'AEO:rank_fifteen:coordinate-8'
    error stop
  end if
  checks=checks+1
  ! (3,-2,5,8,9,10,11,12,13,14,15,16,17,18,-5) has Table 9.1 position 1.
  ! Arithmetic: 1 = 1; dimensions 4:14 have zero deltas.
  if (a(3,-2,5,8,9,10,11,12,13,14, &
       15,16,17,18,-5) /= '3,-2,5,8,9,10,11,12,13,14,15,16,17,18,-5') then
    write(*,'(a)') 'AEO:rank_fifteen:coordinate-1'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'AEO:rank_fifteen:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER RANK FIFTEEN OK'
end program array_element_order_rank_fifteen_effect
