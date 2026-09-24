program intrinsics_16_9_j_fraction_result_kind
  implicit none
  integer :: checks
  integer, parameter :: rk = kind(0.0d0)
  real(rk) :: high
  checks=0
  high = 1.0_rk
  if (kind(fraction(high)) /= kind(high)) then
    write(*,'(a)') 'I16J:fraction_result_kind:same-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION RESULT KIND OK'
end program intrinsics_16_9_j_fraction_result_kind
