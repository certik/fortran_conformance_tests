program intrinsics_16_9_b_anint_nearest_values
  implicit none
  integer :: checks
  real :: near_pos, near_neg, tie_pos, tie_neg
  checks=0
  near_pos = anint(2.25)
  near_neg = anint(-2.25)
  tie_pos = anint(2.5)
  tie_neg = anint(-2.5)
  if (near_pos /= 2.0) then
    write(*,'(a)') 'I16B:anint_nearest_values:nearest-positive'
    error stop
  end if
  checks=checks+1
  if (near_neg /= -2.0) then
    write(*,'(a)') 'I16B:anint_nearest_values:nearest-negative'
    error stop
  end if
  checks=checks+1
  if (tie_pos /= 3.0) then
    write(*,'(a)') 'I16B:anint_nearest_values:tie-positive'
    error stop
  end if
  checks=checks+1
  if (tie_neg /= -3.0) then
    write(*,'(a)') 'I16B:anint_nearest_values:tie-negative'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'I16B:anint_nearest_values:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ANINT NEAREST VALUES OK'
end program intrinsics_16_9_b_anint_nearest_values
