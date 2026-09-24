program intrinsics_16_9_b_aint_truncation_values
  implicit none
  integer :: checks
  real :: below_one, positive, negative
  checks=0
  below_one = aint(0.5)
  positive = aint(2.5)
  negative = aint(-2.5)
  if (below_one /= 0.0) then
    write(*,'(a)') 'I16B:aint_truncation_values:below-one-zero'
    error stop
  end if
  checks=checks+1
  if (positive /= 2.0) then
    write(*,'(a)') 'I16B:aint_truncation_values:positive-toward-zero'
    error stop
  end if
  checks=checks+1
  if (negative /= -2.0) then
    write(*,'(a)') 'I16B:aint_truncation_values:negative-toward-zero'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16B:aint_truncation_values:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B AINT TRUNCATION VALUES OK'
end program intrinsics_16_9_b_aint_truncation_values
