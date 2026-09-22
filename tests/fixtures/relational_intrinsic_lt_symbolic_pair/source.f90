! rule: S10.1.5.5.1-002
! covers: lt-symbolic-pair
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_lt_symbolic_pair
  implicit none
  integer :: checks
  integer :: less_left, less_right, equal_left, equal_right, greater_left, greater_right
  logical :: dotted_less, symbolic_less, dotted_equal, symbolic_equal
  logical :: dotted_greater, symbolic_greater
  checks=0
  less_left = -4
  less_right = 3
  ! less row: -4 is less than 3; less than is true on this row.
  equal_left = 5
  equal_right = 5
  ! equal row: 5 is equal to 5; less than is false on this row.
  greater_left = 8
  greater_right = 1
  ! greater row: 8 is greater than 1; less than is false on this row.
  dotted_less = less_left .LT. less_right
  if (.not. (dotted_less)) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:dotted-less-control'
    error stop
  end if
  checks=checks+1
  symbolic_less = less_left < less_right
  if (.not. (symbolic_less)) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:symbolic-less-control'
    error stop
  end if
  checks=checks+1
  if (dotted_less .neqv. symbolic_less) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:less-spellings-agree'
    error stop
  end if
  checks=checks+1
  dotted_equal = equal_left .LT. equal_right
  if (dotted_equal) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:dotted-equal-control'
    error stop
  end if
  checks=checks+1
  symbolic_equal = equal_left < equal_right
  if (symbolic_equal) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:symbolic-equal-control'
    error stop
  end if
  checks=checks+1
  if (dotted_equal .neqv. symbolic_equal) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:equal-spellings-agree'
    error stop
  end if
  checks=checks+1
  dotted_greater = greater_left .LT. greater_right
  if (dotted_greater) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:dotted-greater-control'
    error stop
  end if
  checks=checks+1
  symbolic_greater = greater_left < greater_right
  if (symbolic_greater) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:symbolic-greater-control'
    error stop
  end if
  checks=checks+1
  if (dotted_greater .neqv. symbolic_greater) then
    write(*,'(a)') 'RIF:lt_symbolic_pair:greater-spellings-agree'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (9)
  case default
    write(*,'(a)') 'RIF:lt_symbolic_pair:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC LT SYMBOLIC PAIR OK'
end program rel_intrinsic_lt_symbolic_pair
