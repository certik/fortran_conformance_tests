program intrinsics_16_9_b_asin_result_characteristics
  implicit none
  integer :: checks
  real(kind=kind(0.0d0)) :: high_inputs(2)
  complex :: z
  checks=0
  high_inputs = [-1.0d0, 1.0d0]
  z = (0.5, 0.75)
  if (kind(asin(high_inputs(1))) /= kind(high_inputs(1))) then
    write(*,'(a)') 'I16B:asin_result_characteristics:real-kind'
    error stop
  end if
  checks=checks+1
  if (size(asin(high_inputs)) /= 2) then
    write(*,'(a)') 'I16B:asin_result_characteristics:real-size'
    error stop
  end if
  checks=checks+1
  if (kind(asin(z)) /= kind(z)) then
    write(*,'(a)') 'I16B:asin_result_characteristics:complex-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16B:asin_result_characteristics:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIN RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_b_asin_result_characteristics
