! rule: S9.5.3.3-001
! covers: position-determined-by-subscript-order-value
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_position_rank_two_effect
  implicit none
  integer :: checks
  integer :: a(5:7,20:23)
  data a / &
    5070, &
    6070, &
    7070, &
    5071, &
    6071, &
    7071, &
    5072, &
    6072, &
    7072, &
    5073, &
    6073, &
    7073 /
  checks=0
  ! rank 2 positions: j1=5,j2=20,d1=3; selected positions are interior.
  ! (6,21) position 5: 1+(6-(5))+(21-20)*3 = 5.
  if (a(6,21) /= 6071) then
    write(*,'(a)') 'AEO:position_rank_two:coordinate-6-21'
    error stop
  end if
  checks=checks+1
  ! (5,22) position 7: 1+(5-(5))+(22-20)*3 = 7.
  if (a(5,22) /= 5072) then
    write(*,'(a)') 'AEO:position_rank_two:coordinate-5-22'
    error stop
  end if
  checks=checks+1
  ! (7,22) position 9: 1+(7-(5))+(22-20)*3 = 9.
  if (a(7,22) /= 7072) then
    write(*,'(a)') 'AEO:position_rank_two:coordinate-7-22'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'AEO:position_rank_two:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER POSITION RANK TWO OK'
end program array_element_order_position_rank_two_effect
