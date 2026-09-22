! rule: S9.5.3.3-002
! covers: rank-one-order-value
! Oracle constants are hand-computed from Fortran 2023 Table 9.1.
! The DATA list is already in that formula order; no storage-layout oracle is used.
program array_element_order_rank_one_effect
  implicit none
  integer :: checks
  integer :: a(3:7)
  data a / &
    103, &
    104, &
    105, &
    106, &
    107 /
  checks=0
  ! rank 1: j1=3, s1=5 gives position 1+(5-3)=3; DATA value 105.
  if (a(5) /= 105) then
    write(*,'(a)') 'AEO:rank_one:s1-five-position-three'
    error stop
  end if
  checks=checks+1
  ! endpoint controls keep the nonunit lower-bound mapping visible.
  if (a(3) /= 103) then
    write(*,'(a)') 'AEO:rank_one:lower-bound-control'
    error stop
  end if
  checks=checks+1
  if (a(7) /= 107) then
    write(*,'(a)') 'AEO:rank_one:upper-bound-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'AEO:rank_one:check-total'
    error stop
  end if
  write(*,'(a)') 'ARRAY ELEMENT ORDER RANK ONE OK'
end program array_element_order_rank_one_effect
