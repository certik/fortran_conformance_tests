program intrinsics_16_9_b_asind_result_characteristics
  implicit none
  integer :: checks
  real(kind=kind(0.0d0)) :: high_inputs(2)
  checks=0
  high_inputs = [-1.0d0, 1.0d0]
  if (kind(asind(high_inputs(1))) /= kind(high_inputs(1))) then
    write(*,'(a)') 'I16B:asind_result_characteristics:real-kind'
    error stop
  end if
  checks=checks+1
  if (size(asind(high_inputs)) /= 2) then
    write(*,'(a)') 'I16B:asind_result_characteristics:real-size'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asind_result_characteristics:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIND RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_b_asind_result_characteristics
