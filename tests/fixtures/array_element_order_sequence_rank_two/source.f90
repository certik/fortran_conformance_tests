! rule: S9.5.3.3-001
! covers: array-elements-form-sequence
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_sequence_rank_two_effect
  implicit none
  integer :: checks
  integer :: a(2:4,-1:2)
  data a / &
    2049, &
    3049, &
    4049, &
    2050, &
    3050, &
    4050, &
    2051, &
    3051, &
    4051, &
    2052, &
    3052, &
    4052 /
  checks=0
  ! rank 2 sequence: j1=2,j2=-1,d1=3; order is (2,-1),(3,-1),(4,-1), then s2 advances.
  ! (2,-1) position 1: 1+(2-2)+(-1-(-1))*3 = 1.
  if (a(2,-1) /= 2049) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-2--1'
    error stop
  end if
  checks=checks+1
  ! (3,-1) position 2: 1+(3-2)+(-1-(-1))*3 = 2.
  if (a(3,-1) /= 3049) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-3--1'
    error stop
  end if
  checks=checks+1
  ! (4,-1) position 3: 1+(4-2)+(-1-(-1))*3 = 3.
  if (a(4,-1) /= 4049) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-4--1'
    error stop
  end if
  checks=checks+1
  ! (2,0) position 4: 1+(2-2)+(0-(-1))*3 = 4.
  if (a(2,0) /= 2050) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-2-0'
    error stop
  end if
  checks=checks+1
  ! (3,0) position 5: 1+(3-2)+(0-(-1))*3 = 5.
  if (a(3,0) /= 3050) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-3-0'
    error stop
  end if
  checks=checks+1
  ! (4,0) position 6: 1+(4-2)+(0-(-1))*3 = 6.
  if (a(4,0) /= 4050) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-4-0'
    error stop
  end if
  checks=checks+1
  ! (2,1) position 7: 1+(2-2)+(1-(-1))*3 = 7.
  if (a(2,1) /= 2051) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-2-1'
    error stop
  end if
  checks=checks+1
  ! (3,1) position 8: 1+(3-2)+(1-(-1))*3 = 8.
  if (a(3,1) /= 3051) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-3-1'
    error stop
  end if
  checks=checks+1
  ! (4,1) position 9: 1+(4-2)+(1-(-1))*3 = 9.
  if (a(4,1) /= 4051) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-4-1'
    error stop
  end if
  checks=checks+1
  ! (2,2) position 10: 1+(2-2)+(2-(-1))*3 = 10.
  if (a(2,2) /= 2052) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-2-2'
    error stop
  end if
  checks=checks+1
  ! (3,2) position 11: 1+(3-2)+(2-(-1))*3 = 11.
  if (a(3,2) /= 3052) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-3-2'
    error stop
  end if
  checks=checks+1
  ! (4,2) position 12: 1+(4-2)+(2-(-1))*3 = 12.
  if (a(4,2) /= 4052) then
    write(*,'(a)') 'AEO:sequence_rank_two:coordinate-4-2'
    error stop
  end if
  checks=checks+1
  if (checks /= 12) then
    write(*,'(a)') 'AEO:sequence_rank_two:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER SEQUENCE RANK TWO OK'
end program array_element_order_sequence_rank_two_effect
